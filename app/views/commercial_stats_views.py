"""Commercial statistics based on request cohorts and recorded signatures."""
from statistics import mean

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from app.models import EmailTracking, Event
from app.module.lib_graph.commercial_pipeline import prepare_quote_graphs
from app.views.private_api_data import filter_dates


RELANCE_STATUS = {
    "First Rappel": "Première relance", "Last Rappel": "Dernière relance",
    "Prolongation": "Prolongation", "Temoignage": "Témoignage",
    "Phonebooth Offert": "Phonebooth offert", "Last Chance": "Dernière offre",
}
SENT_STATUS = {"Sended", "Resended", "Refused", "Acompte OK", "Presta FINI",
               "Post Presta", "Sent Media", "Media KO"} | set(RELANCE_STATUS)
DONE_STATUS = {"Presta FINI", "Post Presta", "Sent Media", "Media KO"}
LABELS = dict(Event.STATUS)
LABELS.update(RELANCE_STATUS)
LABELS.update({"Initied": "Nouvelle demande", "Calculed": "Devis calculé",
               "Sended": "Devis envoyé", "Resended": "Devis renvoyé",
               "Acompte OK": "Réservation confirmée", "Refused": "Refusé",
               "Presta FINI": "Prestation terminée", "Post Presta": "Suivi après prestation",
               "Sent Media": "Médias envoyés", "Pending": "En attente", "Media KO": "Médias à vérifier"})


def percent(part, total):
    return round(100 * part / total, 2) if total else None


def amount(event, signed=False):
    # A zero amount is a real value; don't replace it with a fallback.
    if signed and event.prix_valided is not None:
        return event.prix_valided
    return event.prix_proposed if event.prix_proposed is not None else 0


def summarise(events, processed_ids):
    processed = [event for event in events if event.id in processed_ids]
    signed = [event for event in processed if event.signer_at is not None]
    refused = [event for event in processed if event.signer_at is None and event.status == "Refused"]
    pending = [event for event in processed if event.signer_at is None and event.status != "Refused"]
    delays = [(event.signer_at - event.created_at).total_seconds() / 86400 for event in signed if event.signer_at >= event.created_at]
    total_signed = sum(amount(event, signed=True) for event in signed)
    return {
        "requests": len(events), "processed": len(processed), "signed": len(signed),
        "refused": len(refused), "pending": len(pending),
        "conversion": percent(len(signed), len(processed)),
        "conversion_decided": percent(len(signed), len(signed) + len(refused)),
        "signed_amount": total_signed,
        "pending_amount": sum(amount(event) for event in pending),
        "refused_amount": sum(amount(event) for event in refused),
        "average_signed": round(total_signed / len(signed), 2) if signed else None,
        "average_delay": round(mean(delays), 1) if delays else None,
        "delay_count": len(delays), "invalid_delays": len(signed) - len(delays),
    }


def commercial_report(request):
    queryset = Event.objects.select_related("client", "event_details", "event_acompte")
    queryset = filter_dates(request, queryset, "created_at", with_time=True)
    segment = request.GET.get("segment", "all")
    if segment not in ("all", "individual", "business"):
        raise ValueError("Choisissez tous les clients, particuliers ou entreprises.")
    if segment != "all":
        queryset = queryset.filter(client__raison_sociale=(segment == "business"))
    events = list(queryset.order_by("id"))
    # A subquery avoids a large IN parameter list with historical CRM data.
    tracked_statuses = {}
    for event_id, status in EmailTracking.objects.filter(event_traced__in=queryset.values("id")).exclude(delivery_status__in=["preparing", "error", "refused"]).values_list("event_traced", "status_devis"):
        tracked_statuses.setdefault(event_id, set()).add(status)
    processed_ids = set()
    histories = {}
    for event in events:
        statuses = {value.strip() for value in (event.history_status or "").split(",") if value.strip()}
        statuses.add(event.status)
        statuses.update(tracked_statuses.get(event.id, set()))
        histories[event.id] = statuses
        if event.signer_at is not None or event.id in tracked_statuses or statuses & SENT_STATUS:
            processed_ids.add(event.id)
    totals = summarise(events, processed_ids)
    statuses = []
    for status in sorted({event.status or "" for event in events}):
        group = [event for event in events if (event.status or "") == status]
        statuses.append({"label": LABELS.get(status, status or "Non renseigné"),
                         "count": len(group), "share": percent(len(group), len(events)),
                         "amount": sum(amount(event, signed=event.signer_at is not None) for event in group)})
    segments = []
    for business, label in ((False, "Particuliers"), (True, "Entreprises")):
        group = [event for event in events if event.client.raison_sociale == business]
        segments.append({"label": label, **summarise(group, processed_ids)})
    relances = []
    for status, label in RELANCE_STATUS.items():
        group = [event for event in events if status in histories[event.id]]
        signed = sum(event.signer_at is not None for event in group)
        relances.append({"label": label, "count": len(group), "signed": signed,
                         "conversion": percent(signed, len(group))})
    outstanding = [event for event in events if event.status in DONE_STATUS and event.event_acompte and (event.event_acompte.montant_restant or 0) > 0]
    outstanding.sort(key=lambda event: event.event_details.date_evenement)
    totals["outstanding_count"] = len(outstanding)
    totals["outstanding_amount"] = sum(event.event_acompte.montant_restant for event in outstanding)
    return {
        **prepare_quote_graphs(events, processed_ids, amount),
        "totals": totals, "statuses": statuses, "segments": segments, "relances": relances,
        "outstanding": outstanding[:30], "outstanding_more": max(0, len(outstanding) - 30),
        "unsigned_confirmed": sum(event.signer_at is None and event.status in (DONE_STATUS | {"Acompte OK"}) for event in events),
        "missing_amounts": sum(event.prix_proposed is None and (event.signer_at is None or event.prix_valided is None) for event in events),
    }


@never_cache
@staff_member_required(login_url="login")
@require_GET
def graph_commercial_stats(request):
    context = {"start_date": request.GET.get("start_date", ""),
               "end_date": request.GET.get("end_date", ""),
               "segment": request.GET.get("segment", "all")}
    try:
        context.update(commercial_report(request))
    except ValueError as exc:
        context["error"] = str(exc)
        return render(request, "app/backend/graph/graph_commercial_stats.html", context, status=400)
    return render(request, "app/backend/graph/graph_commercial_stats.html", context)
