"""Graph-ready CRM quotation statistics, using existing Event objects only.

The cohort is the date on which a quotation request was created. Only
processed quotations count towards signed / pending / refused metrics.
No monetary figure here represents actual cash received.
"""
from django.utils import timezone
from app.views.private_api import PARIS_TIME_ZONE


MONTHS = ("Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août",
          "Sep", "Oct", "Nov", "Déc")
AGE_LABELS = ("0 à 7 jours", "8 à 14 jours", "15 à 30 jours", "Plus de 30 jours")


def _percent(value, total):
    return round(100 * value / total, 1) if total else 0


def _local_date(value):
    if timezone.is_aware(value):
        return timezone.localtime(value, PARIS_TIME_ZONE).date()
    return value.date()


def prepare_quote_graphs(events, processed_ids, amount, today=None):
    """Return graph series and a short actionable list without extra DB queries."""
    if today is None:
        today = timezone.localtime(timezone.now(), PARIS_TIME_ZONE).date()

    months = {}
    age_groups = [{"label": label, "count": 0, "amount": 0} for label in AGE_LABELS]
    clients = [
        {"label": "Particuliers", "count": 0, "amount": 0},
        {"label": "Entreprises", "count": 0, "amount": 0},
    ]
    portfolio = [
        {"label": "Signés", "count": 0, "amount": 0, "class_name": "signed"},
        {"label": "En attente", "count": 0, "amount": 0, "class_name": "pending"},
        {"label": "Refusés", "count": 0, "amount": 0, "class_name": "refused"},
    ]
    biggest_pending = []

    for event in events:
        if event.id not in processed_ids:
            continue

        created = _local_date(event.created_at)
        key = (created.year, created.month)
        if key not in months:
            months[key] = {
                "label": f"{MONTHS[created.month - 1]} {created.year}",
                "signed": 0, "pending": 0, "refused": 0, "processed": 0,
            }
        month = months[key]
        month["processed"] += 1

        if event.signer_at is not None:
            category = "signed"
            index = 0
        elif event.status == "Refused":
            category = "refused"
            index = 2
        else:
            category = "pending"
            index = 1

        month[category] += 1
        value = amount(event, signed=(category == "signed"))
        portfolio[index]["count"] += 1
        portfolio[index]["amount"] += value

        if category != "pending":
            continue

        days = max(0, (today - created).days)
        age_index = 0 if days <= 7 else 1 if days <= 14 else 2 if days <= 30 else 3
        age_groups[age_index]["count"] += 1
        age_groups[age_index]["amount"] += value

        client_index = 1 if event.client.raison_sociale else 0
        clients[client_index]["count"] += 1
        clients[client_index]["amount"] += value
        biggest_pending.append({"event": event, "amount": value, "days": days})

    # Display the most recent twelve months of the selected cohort.
    recent_months = [months[key] for key in sorted(months)[-12:]]
    max_month = max(
        (month[category] for month in recent_months
         for category in ("signed", "pending", "refused")),
        default=0,
    )
    for month in recent_months:
        for category in ("signed", "pending", "refused"):
            month[category + "_height"] = _percent(month[category], max_month)
        month["conversion"] = _percent(month["signed"], month["processed"])

    for rows in (age_groups, clients):
        max_value = max((max(0, row["amount"]) for row in rows), default=0)
        for row in rows:
            row["width"] = _percent(max(0, row["amount"]), max_value)

    positive_total = sum(max(0, row["amount"]) for row in portfolio)
    for row in portfolio:
        row["width"] = _percent(max(0, row["amount"]), positive_total)

    biggest_pending.sort(key=lambda row: (-row["amount"], -row["days"], row["event"].id))

    return {
        "quote_months": recent_months,
        "quote_months_hidden": max(0, len(months) - len(recent_months)),
        "quote_ages": age_groups,
        "quote_clients": clients,
        "quote_portfolio": portfolio,
        "quote_top_pending": biggest_pending[:10],
        "quote_pending_more": max(0, len(biggest_pending) - 10),
    }
