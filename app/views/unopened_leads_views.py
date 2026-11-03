"""A manual follow-up queue: opening is a signal, never proof of receipt."""
import re
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Exists, F, OuterRef, Q, Subquery
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from app.models import EmailTracking, Event, EventRelance


QUOTE_TYPES = ["devis", "rappel_devis", "last_rappel_devis", "prolongation_devis",
               "temoingnage_client_devis", "phonebooth_offert_devis", "last_chance_devis"]
LEAD_STATUSES = ["Initied", "Calculed", "Sended", "Resended", "Last Chance", "First Rappel",
                 "Last Rappel", "Prolongation", "Temoignage", "Phonebooth Offert", "Pending"]
ISSUES = ["refused", "error", "unknown", "delayed", "bounced"]
CHANNELS = {"phone": "Appel", "email": "Mail manuel", "other": "Autre contact"}


def lead_queryset():
    now = timezone.now()
    quote_type = Q(mail_type__in=QUOTE_TYPES) | Q(mail_type="", opening_tracked=True)
    quotes = EmailTracking.objects.filter(quote_type, event_traced=OuterRef("pk")).exclude(delivery_status="preparing")
    latest = quotes.order_by("-sent_at", "-id")
    contacts = EventRelance.objects.filter(event_id=OuterRef("pk"), date_relance__lte=now).order_by("-date_relance", "-id")
    return Event.objects.select_related("client", "event_details", "event_product", "event_option").filter(
        signer_at__isnull=True, status__in=LEAD_STATUSES, client__autorisation_mail=True,
        event_details__date_evenement__gte=timezone.localdate(),
    ).annotate(
        last_quote_id=Subquery(latest.values("id")[:1]),
        last_quote_sent=Subquery(latest.values("sent_at")[:1]),
        last_quote_state=Subquery(latest.values("delivery_status")[:1]),
        last_quote_recipient=Subquery(latest.values("recipient")[:1]),
        last_quote_diagnostic=Subquery(latest.values("diagnostic")[:1]),
        has_opened_quote=Exists(quotes.filter(opened=True)),
        last_contact_at=Subquery(contacts.values("date_relance")[:1]),
        last_contact_note=Subquery(contacts.values("commentaire")[:1]),
        last_contact_by=Subquery(contacts.values("membre")[:1]),
    ).filter(last_quote_id__isnull=False)


@never_cache
@staff_member_required(login_url="login")
@require_http_methods(["GET", "POST"])
def unopened_leads(request):
    if request.method == "POST":
        try:
            event_id = int(request.POST.get("event_id", ""))
            qualification = int(request.POST.get("qualification", "0"))
        except ValueError:
            return HttpResponseBadRequest("Dossier ou qualification invalide.")
        note = request.POST.get("commentaire", "").strip()
        channel = request.POST.get("channel", "phone")
        if channel not in CHANNELS or not 0 <= qualification <= 5 or not note or len(note) > 2000:
            return HttpResponseBadRequest("Renseignez un compte rendu de 1 à 2000 caractères et une qualification entre 0 et 5.")
        # Recheck the record: a signed/refused/opted-out lead must not be reactivated.
        event = get_object_or_404(lead_queryset(), pk=event_id)
        EventRelance.objects.create(event=event, membre=request.user.get_username(), date_relance=timezone.now(),
                                   qualification=qualification, commentaire=f"{CHANNELS[channel]} · Suivi devis : {note}")
        # Keep the current local path; no user-controlled redirect destination.
        return redirect(request.path + ("?" + request.GET.urlencode() if request.GET else ""))

    bucket = request.GET.get("bucket", "unopened")
    followup = request.GET.get("followup", "todo")
    segment = request.GET.get("segment", "all")
    age = request.GET.get("age", "24")
    if bucket not in ("unopened", "issues") or followup not in ("todo", "done", "all") or segment not in ("all", "business", "individual") or age not in ("0", "24", "48", "72", "168"):
        return HttpResponseBadRequest("Filtre de relance invalide.")
    queryset = lead_queryset().filter(last_quote_sent__lte=timezone.now() - timedelta(hours=int(age)))
    term = request.GET.get("q", "").strip()[:200]
    if term:
        queryset = queryset.filter(Q(client__nom__icontains=term) | Q(client__mail__icontains=term) | Q(client__numero_telephone__icontains=term) | Q(event_details__ville_evenement__icontains=term))
    if segment != "all":
        queryset = queryset.filter(client__raison_sociale=(segment == "business"))
    if followup == "todo":
        queryset = queryset.filter(Q(last_contact_at__isnull=True) | Q(last_contact_at__lt=F("last_quote_sent")))
    elif followup == "done":
        queryset = queryset.filter(last_contact_at__gte=F("last_quote_sent"))
    unopened = queryset.filter(has_opened_quote=False, last_quote_state__in=["legacy", "accepted", "delivered"])
    issues = queryset.filter(last_quote_state__in=ISSUES)
    counts = {"unopened": unopened.count(), "issues": issues.count()}
    selected = unopened if bucket == "unopened" else issues
    page = Paginator(selected.order_by("last_quote_sent", "event_details__date_evenement", "id"), 25).get_page(request.GET.get("page"))
    for event in page:
        event.quote_state_label = dict(EmailTracking.DELIVERY_STATUS).get(event.last_quote_state, event.last_quote_state)
        event.call_number = re.sub(r"[^0-9+]", "", event.client.numero_telephone or "")
    params = request.GET.copy()
    params.pop("page", None)
    links = {}
    for target in ("unopened", "issues"):
        values = params.copy()
        values["bucket"] = target
        links[target] = "?" + values.urlencode()
    return render(request, "app/backend/unopened_leads.html", {
        "page": page, "bucket": bucket, "followup": followup, "segment": segment,
        "age": age, "q": term, "counts": counts, "links": links, "query": params.urlencode(),
    })
