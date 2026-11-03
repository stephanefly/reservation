"""Graph-ready CRM quotation statistics, using existing Event objects only.

The cohort is the date on which a quotation request was created. Only
processed quotations count towards signed / pending / refused metrics.
No monetary figure here represents actual cash received.
"""
from django.utils import timezone
from app.views.private_api import PARIS_TIME_ZONE


AGE_LABELS = ("0 à 7 jours", "8 à 14 jours", "15 à 30 jours", "Plus de 30 jours")


def _percent(value, total):
    return round(100 * value / total, 1) if total else 0


def _local_date(value):
    if timezone.is_aware(value):
        return timezone.localtime(value, PARIS_TIME_ZONE).date()
    return value.date()



def _empty_period(label):
    return {
        "label": label,
        "signed": 0, "pending": 0, "refused": 0, "processed": 0,
        "signed_amount": 0, "pending_amount": 0, "refused_amount": 0,
    }


def _finish_periods(periods, limit):
    rows = [periods[key] for key in sorted(periods)[-limit:]]
    peak = max(
        (row[category] for row in rows
         for category in ("signed", "pending", "refused")),
        default=0,
    )
    for row in rows:
        for category in ("signed", "pending", "refused"):
            row[category + "_height"] = _percent(row[category], peak)
        row["conversion"] = _percent(row["signed"], row["processed"])
    return rows

def prepare_quote_graphs(events, processed_ids, amount, today=None):
    """Return graph series and a short actionable list without extra DB queries."""
    if today is None:
        today = timezone.localtime(timezone.now(), PARIS_TIME_ZONE).date()

    years = {}
    semesters = {}
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
        semester = 1 if created.month <= 6 else 2
        if created.year not in years:
            years[created.year] = _empty_period(str(created.year))
        key = (created.year, semester)
        if key not in semesters:
            semesters[key] = _empty_period(f"{created.year} · S{semester}")

        if event.signer_at is not None:
            category = "signed"
            index = 0
        elif event.status == "Refused":
            category = "refused"
            index = 2
        else:
            category = "pending"
            index = 1

        value = amount(event, signed=(category == "signed"))
        for period in (years[created.year], semesters[key]):
            period["processed"] += 1
            period[category] += 1
            period[category + "_amount"] += value
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

    # Comparisons use the request creation date, with local Paris semester bounds.
    annual = _finish_periods(years, limit=10)
    half_year = _finish_periods(semesters, limit=12)

    for rows in (age_groups, clients):
        max_value = max((max(0, row["amount"]) for row in rows), default=0)
        for row in rows:
            row["width"] = _percent(max(0, row["amount"]), max_value)

    positive_total = sum(max(0, row["amount"]) for row in portfolio)
    for row in portfolio:
        row["width"] = _percent(max(0, row["amount"]), positive_total)

    biggest_pending.sort(key=lambda row: (-row["amount"], -row["days"], row["event"].id))

    return {
        "quote_periods": [
            {"title": "Évolution annuelle des devis traités",
             "subtitle": "Comparaison par année civile",
             "rows": annual, "hidden": max(0, len(years) - len(annual)),
             "hidden_label": "années"},
            {"title": "Évolution semestrielle des devis traités",
             "subtitle": "S1 : janvier–juin · S2 : juillet–décembre",
             "rows": half_year, "hidden": max(0, len(semesters) - len(half_year)),
             "hidden_label": "semestres"},
        ],
        "quote_ages": age_groups,
        "quote_clients": clients,
        "quote_portfolio": portfolio,
        "quote_top_pending": biggest_pending[:10],
        "quote_pending_more": max(0, len(biggest_pending) - 10),
    }
