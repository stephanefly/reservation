"""Read-only commercial insights built from the CRM's existing records.

No schema change, guessed loss reasons or automatic contact. Amounts of
multi-product quotations are *associated* with each product, not allocated.
"""
from django.utils import timezone
from app.views.private_api import PARIS_TIME_ZONE


PRODUCTS = (
    ("photobooth", "Photobooth"),
    ("miroirbooth", "Miroirbooth"),
    ("videobooth", "360Booth"),
    ("voguebooth", "Voguebooth"),
    ("ipadbooth", "iPadBooth"),
    ("airbooth", "Airbooth"),
)
QUOTE_MAIL_TYPES = {
    "devis", "rappel_devis", "last_rappel_devis", "prolongation_devis",
    "temoingnage_client_devis", "phonebooth_offert_devis", "last_chance_devis",
}
QUOTE_STATUSES = {
    "Sended", "Resended", "First Rappel", "Last Rappel",
    "Last Chance", "Prolongation", "Temoignage", "Phonebooth Offert",
}
# A bounce is still an attempted SMTP submission, not a delivered email.
SUBMITTED_STATES = {"legacy", "accepted", "delivered", "delayed", "bounced"}
LOSS_BANDS = (
    (500, "Moins de 500 €"),
    (1000, "500 à 999 €"),
    (2000, "1 000 à 1 999 €"),
    (None, "2 000 € et plus"),
)


def percent(part, total):
    return round(100 * part / total, 1) if total else 0


def local_date(value):
    if value is None:
        return None
    if timezone.is_aware(value):
        return timezone.localtime(value, PARIS_TIME_ZONE).date()
    return value.date()


def is_quote_tracking(mail_type, status):
    """Legacy quote tracks often have an empty mail_type."""
    return mail_type in QUOTE_MAIL_TYPES or (
        not mail_type and status in QUOTE_STATUSES
    )


def _score(event, value, opened, contact, today):
    """Explainable prioritization, not a statistical conversion probability."""
    event_date = event.event_details.date_evenement
    days_until = (event_date - today).days
    age = max(0, (today - local_date(event.created_at)).days)
    score = 0

    if value >= 2000:
        score += 25
    elif value >= 900:
        score += 18
    elif value >= 500:
        score += 10

    if days_until <= 14:
        score += 25
    elif days_until <= 45:
        score += 18
    elif days_until <= 90:
        score += 10

    if 2 <= age <= 30:
        score += 10
    elif age > 30:
        score += 6

    if opened:
        score += 10  # Email pixel is a weak indicator, not proof of reading.

    if contact:
        score += min(max(int(contact["qualification"] or 0), 0), 5) * 4
        last_contact = local_date(contact["date_relance"])
        if last_contact is not None and 0 <= (today - last_contact).days <= 3:
            score -= 15

    score = max(0, min(100, score))
    if score >= 60:
        label = "Élevée"
    elif score >= 35:
        label = "Moyenne"
    else:
        label = "À examiner"
    return score, label, days_until


def prepare_commercial_insights(events, processed_ids, mail_signals, last_contacts,
                                amount, today=None):
    """Build the funnel, multi-product performance, explicit refusals and call queue."""
    if today is None:
        today = timezone.localtime(timezone.now(), PARIS_TIME_ZONE).date()

    stages = [
        {"label": "Demandes reçues", "count": len(events),
         "note": "Toutes les demandes de la période"},
        {"label": "Devis traités", "count": len(processed_ids),
         "note": "Statut, signature ou historique d'envoi enregistré"},
        {"label": "Envois de devis enregistrés", "count": 0,
         "note": "Envoi SMTP déclaré ou ancien suivi, sans garantie de livraison"},
        {"label": "Ouvertures détectées", "count": 0,
         "note": "Pixel de suivi : lecture non garantie"},
        {"label": "Devis signés", "count": 0,
         "note": "Date de signature renseignée"},
    ]
    products = [
        {"field": field, "label": label, "requests": 0, "processed": 0,
         "signed": 0, "pending": 0, "refused": 0,
         "signed_amount": 0, "pending_amount": 0, "refused_amount": 0}
        for field, label in PRODUCTS
    ]
    loss_segments = [
        {"label": "Particuliers", "count": 0, "amount": 0},
        {"label": "Entreprises", "count": 0, "amount": 0},
    ]
    loss_bands = [
        {"label": label, "count": 0, "amount": 0}
        for _, label in LOSS_BANDS
    ]
    losses = []
    leads = []
    missing_products = 0
    signed_count = 0
    refused_count = 0

    for event in events:
        tracked = mail_signals.get(event.id, {})
        if tracked.get("sent"):
            stages[2]["count"] += 1
        if tracked.get("opened"):
            stages[3]["count"] += 1
        signed = event.signer_at is not None
        if signed:
            signed_count += 1
            stages[4]["count"] += 1

        processed = event.id in processed_ids
        refused = processed and not signed and event.status == "Refused"
        pending = processed and not signed and not refused
        value = amount(event, signed=signed)

        if event.event_product is None:
            missing_products += 1
        else:
            for row in products:
                if not getattr(event.event_product, row["field"], False):
                    continue
                row["requests"] += 1
                if not processed:
                    continue
                row["processed"] += 1
                if signed:
                    row["signed"] += 1
                    row["signed_amount"] += value
                elif refused:
                    row["refused"] += 1
                    row["refused_amount"] += value
                else:
                    row["pending"] += 1
                    row["pending_amount"] += value

        if refused:
            refused_count += 1
            client_index = 1 if event.client.raison_sociale else 0
            loss_segments[client_index]["count"] += 1
            loss_segments[client_index]["amount"] += value
            for index, (ceiling, _) in enumerate(LOSS_BANDS):
                if ceiling is None or value < ceiling:
                    loss_bands[index]["count"] += 1
                    loss_bands[index]["amount"] += value
                    break
            losses.append({"event": event, "amount": value})

        # A call queue is not an instruction to send bulk messages.
        if (pending and event.client.autorisation_mail
                and event.event_details.date_evenement >= today):
            score, label, days_until = _score(
                event, value, tracked.get("opened", False),
                last_contacts.get(event.id), today,
            )
            leads.append({
                "event": event, "amount": value, "score": score,
                "priority": label, "days_until": days_until,
                "opened": tracked.get("opened", False),
                "mail_issue": tracked.get("mail_issue", False),
                "age": max(0, (today - local_date(event.created_at)).days),
            })

    for row in stages:
        row["share"] = percent(row["count"], len(events))
    for row in products:
        row["conversion"] = percent(row["signed"], row["processed"])
        row["refusal_rate"] = percent(row["refused"], row["processed"])

    max_loss = max((row["count"] for row in loss_bands), default=0)
    for row in loss_bands:
        row["width"] = percent(row["count"], max_loss)

    losses.sort(key=lambda row: (-row["amount"], row["event"].id))
    leads.sort(key=lambda row: (-row["score"], -row["amount"], row["event"].id))

    return {
        "insight_funnel": stages,
        "insight_products": products,
        "insight_products_missing": missing_products,
        "insight_loss_count": refused_count,
        "insight_loss_amount": sum(row["amount"] for row in losses),
        "insight_loss_rate": percent(refused_count, len(processed_ids)),
        "insight_loss_segments": loss_segments,
        "insight_loss_bands": loss_bands,
        "insight_loss_top": losses[:10],
        "insight_loss_more": max(0, len(losses) - 10),
        "insight_leads": leads[:20],
        "insight_leads_more": max(0, len(leads) - 20),
        "insight_leads_count": len(leads),
        "insight_signed_count": signed_count,
    }
