"""Administration privée des devis automatiques et simulation PDF sans écriture."""

from copy import copy

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from app.models import Event
from app.module.devis_pdf.generate_pdf import generate_pdf_devis
from .catalog import PACKS, PRODUITS
from .engine import analyse_quote
from .forms import QuoteControlForm
from .models import AutoQuoteSettings, AutoQuoteLog


def event_queryset():
    return Event.objects.select_related(
        "client", "event_product", "event_option", "event_details",
    )


@staff_member_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def admin_quotes(request):
    config, _ = AutoQuoteSettings.objects.get_or_create(pk=1)
    form = QuoteControlForm(
        request.POST if request.method == "POST" else None,
        config=config,
    )
    if request.method == "POST" and form.is_valid():
        form.save_to_config(config)
        return redirect(reverse("admin_auto_quotes") + "?saved=1")

    preview = None
    event = None
    event_id = (request.GET.get("event") or "").strip()
    if event_id.isdigit():
        event = event_queryset().filter(pk=int(event_id)).first()
        if event is None:
            preview = {"eligible": False, "reason": "Devis introuvable"}
        else:
            preview = analyse_quote(event, config, preview=True)

    # Apercu : presenter des dossiers reels et recents, sans demander
    # a l'equipe de retrouver un identifiant technique.
    # Lecture seule : aucun calcul n'est stocke et aucun e-mail n'est envoye.
    recent_events = list(event_queryset().order_by("-created_at", "-pk")[:8])

    logs = list(AutoQuoteLog.objects.order_by("-created_at")[:40])
    product_rows = [
        {"key": key, "label": label, "field": form["product_" + key]}
        for key, label in PRODUITS
    ]
    pack_rows = [
        {"key": pack[0], "label": pack[1], "field": form["pack_" + pack[0]]}
        for pack in PACKS
    ]
    return render(request, "quote_control/dashboard.html", {
        "config": config,
        "form": form,
        "product_rows": product_rows,
        "pack_rows": pack_rows,
        "logs": logs,
        "error_count": AutoQuoteLog.objects.filter(outcome="error").count(),
        "sent_count": AutoQuoteLog.objects.filter(outcome="sent").count(),
        "manual_count": AutoQuoteLog.objects.filter(outcome="manual").count(),
        "preview": preview,
        "preview_event": event,
        "recent_events": recent_events,
        "saved": request.GET.get("saved") == "1",
    })


@staff_member_required(login_url="/login/")
@require_GET
def preview_pdf(request, event_id):
    config = get_object_or_404(AutoQuoteSettings, pk=1)
    event = get_object_or_404(event_queryset(), pk=event_id)
    analysis = analyse_quote(event, config, preview=True)
    if not analysis["eligible"]:
        raise Http404("Devis non éligible à la génération automatique")

    # Ne pas modifier un devis client existant lors de la simulation.
    temporary_event = copy(event)
    for key, value in analysis["calculation"].items():
        setattr(temporary_event, key, value)
    buffer = generate_pdf_devis(temporary_event)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="apercu-devis-auto.pdf"'
    response["Cache-Control"] = "no-store"
    return response
