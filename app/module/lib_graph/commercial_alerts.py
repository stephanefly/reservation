"""Read-only action alerts for open CRM quotations.

Alerts are signals for a human to check, not proof of delivery or automatic
permission to contact a customer. No database write, scheduler or mail send.
"""
from django.utils import timezone

from app.module.lib_graph.commercial_insights import local_date
from app.views.private_api import PARIS_TIME_ZONE


HIGH_VALUE_EUR = 900
UPCOMING_DAYS = 14
URGENT_DAYS = 7
FOLLOWUP_DAYS = 3

ALERT_TYPES = (
    ("all", "Toutes"),
    ("delivery", "Incidents d'envoi"),
    ("upcoming", "Événements proches"),
    ("followup", "Relances à vérifier"),
    ("high_value", "Devis importants"),
)
MAIL_ISSUE_STATES = {"refused", "error", "unknown", "delayed", "bounced"}
MAIL_TOUCH_STATES = {"accepted", "delivered", "legacy"}


def _last_contact_day(quote, contact):
    """Most recent *recorded* contact; failed/delayed sends do not reset it."""
    dates = []
    if contact and contact.get("date_relance"):
        dates.append(local_date(contact["date_relance"]))
    if quote and quote.get("last_valid_sent"):
        dates.append(local_date(quote["last_valid_sent"]))
    return max(dates) if dates else None


def prepare_commercial_alerts(events, processed_ids, latest_quotes,
                              last_contacts, amount, selected="all", today=None):
    """Return a deduplicated, filtered alert queue and global category counts.

    All non-signed, non-refused processed quotations with future/current events
    are checked; a dossier can match several categories, but is listed once.
    """
    valid = {key for key, _ in ALERT_TYPES}
    if selected not in valid:
        raise ValueError("Choisissez un filtre d'alerte commerciale valide.")

    if today is None:
        today = timezone.localtime(timezone.now(), PARIS_TIME_ZONE).date()

    categories = [
        {"key": key, "label": label, "count": 0}
        for key, label in ALERT_TYPES
    ]
    counts = {row["key"]: 0 for row in categories}
    all_alerts = []

    for event in events:
        if (event.id not in processed_ids or event.signer_at is not None
                or event.status == "Refused"):
            continue
        event_day = event.event_details.date_evenement
        if event_day is None or event_day < today:
            continue

        days_until = (event_day - today).days
        quote = latest_quotes.get(event.id)
        contact = last_contacts.get(event.id)
        last_touch = _last_contact_day(quote, contact)
        created_day = local_date(event.created_at)
        base_day = max(created_day, last_touch) if last_touch else created_day
        days_since_touch = (today - base_day).days
        value = amount(event)

        reasons = []
        matched = set()
        # Use only the most recent quote-specific mail. A prior bounce is
        # superseded by a newer successful attempt, not left as an active alert.
        if quote and quote["delivery_status"] in MAIL_ISSUE_STATES:
            matched.add("delivery")
            state = quote["delivery_status"]
            if state in {"refused", "error", "bounced"}:
                reasons.append("Échec d'envoi à vérifier")
            else:
                reasons.append("Livraison incertaine à vérifier")
        if days_until <= UPCOMING_DAYS:
            matched.add("upcoming")
            reasons.append(f"Événement dans {days_until} j")
        if days_since_touch >= FOLLOWUP_DAYS:
            matched.add("followup")
            if last_touch is None:
                reasons.append(f"Aucun contact récent confirmé depuis {days_since_touch} j")
            else:
                reasons.append(f"Dernier contact enregistré il y a {days_since_touch} j")
        if value >= HIGH_VALUE_EUR:
            matched.add("high_value")
            reasons.append(f"Devis d'au moins {HIGH_VALUE_EUR} €")

        if not matched:
            continue
        counts["all"] += 1
        for key in matched:
            counts[key] += 1

        # Urgency is an ordering heuristic, not a predictive conversion rate.
        critical = "delivery" in matched or days_until <= URGENT_DAYS
        priority = "Urgente" if critical else "À traiter" if (
            "upcoming" in matched or {"followup", "high_value"} <= matched
        ) else "À surveiller"
        rank = 3 if critical else 2 if priority == "À traiter" else 1
        all_alerts.append({
            "event": event,
            "amount": value,
            "days_until": days_until,
            "days_since_touch": max(0, days_since_touch),
            "priority": priority,
            "priority_rank": rank,
            "reasons": reasons,
            "matched": matched,
            "email_allowed": event.client.autorisation_mail,
            "delivery_state": quote["delivery_status"] if quote else None,
        })

    all_alerts.sort(
        key=lambda row: (-row["priority_rank"], row["days_until"],
                         -row["amount"], row["event"].id)
    )
    rows = [
        row for row in all_alerts
        if selected == "all" or selected in row["matched"]
    ]
    for category in categories:
        category["count"] = counts[category["key"]]
        category["selected"] = category["key"] == selected

    return {
        "commercial_alert_categories": categories,
        "commercial_alert_total": len(all_alerts),
        "commercial_alert_rows": rows[:30],
        "commercial_alert_more": max(0, len(rows) - 30),
        "commercial_alert_filtered_count": len(rows),
        "commercial_alert_selected": selected,
        "commercial_alert_as_of": today,
    }
