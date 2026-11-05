"""Catalogue commercial : choix des offres automatisables et simulation fidèle.

Un seul réglage : cocher l'éligibilité sur une machine ou un pack.
Les anciens formulaires de paramétrage ne peuvent plus changer les envois.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .auto_policy import effective_quote_config
from .catalog_forms import CatalogEntryForm
from .models import AutoQuoteLog, AutoQuoteSettings, CatalogEntry
from .price_breakdown import decorate_offers
from .simulation import QuoteSimulationForm


@staff_member_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def admin_catalog(request):
    """Edition catalogue et simulation : aucune autre activation requise."""
    config, _ = AutoQuoteSettings.objects.get_or_create(pk=1)
    simulation_post = (
        request.method == "POST" and request.POST.get("operation") == "simulate"
    )
    legacy_settings_post = request.method == "POST" and (
        request.POST.get("operation") == "settings"
        or request.path.rstrip("/").endswith("/devis-auto")
    )
    active_tab = "simulation" if (
        simulation_post or legacy_settings_post
        or request.GET.get("tab") in ("simulation", "automation")
        or request.GET.get("simulate") == "1"
        or request.GET.get("event", "").isdigit()
    ) else "historique" if request.GET.get("tab") == "historique" else "offres"

    # Les anciens POST de réglages ne réactivent jamais un système parallèle.
    if legacy_settings_post:
        return redirect(reverse("admin_catalog") + "?tab=simulation")

    identifier = (
        request.POST.get("entry") if request.method == "POST" and not simulation_post
        else request.GET.get("edit")
    ) or ""
    identifier = identifier.strip()
    if identifier and not identifier.isdigit():
        raise Http404("Identifiant de catalogue invalide")
    entry = get_object_or_404(CatalogEntry, pk=int(identifier)) if identifier else None
    form = CatalogEntryForm(
        request.POST if request.method == "POST" and not simulation_post else None,
        instance=entry,
    )
    if request.method == "POST" and not simulation_post and form.is_valid():
        saved = form.save()
        return redirect(reverse("admin_catalog") + f"?tab=offres&saved={saved.pk}#edition")

    effective = effective_quote_config(config)
    simulation_form = QuoteSimulationForm(
        request.POST if simulation_post
        else request.GET if request.GET.get("simulate") == "1"
        else None,
    )
    simulation = None
    if simulation_form.is_bound and simulation_form.is_valid():
        simulation = simulation_form.simulate(effective)

    preview = None
    preview_event = None
    event_id = (request.GET.get("event") or "").strip()
    if event_id.isdigit():
        from .engine import analyse_quote
        from .views import event_queryset

        preview_event = event_queryset().filter(pk=int(event_id)).first()
        preview = (
            analyse_quote(preview_event, effective, preview=True)
            if preview_event else {"eligible": False, "reason": "Devis introuvable"}
        )

    all_entries = decorate_offers(CatalogEntry.objects.all())
    if entry is not None:
        entry.pricing = next(
            (x.pricing for x in all_entries if x.pk == entry.pk),
            {"available": False},
        )

    # Ne montrer que les devis réellement signalés comme envoyés
    # par le moteur auto. Les cas manuels et erreurs ne sont pas des envois.
    history = None
    sent_total = 0
    if active_tab == "historique":
        sent_logs = AutoQuoteLog.objects.filter(outcome="sent").order_by(
            "-created_at", "-pk"
        )
        history = Paginator(sent_logs, 25).get_page(request.GET.get("page"))
        sent_total = history.paginator.count
        if history.object_list:
            from app.models import Event

            events = {
                event.pk: event
                for event in Event.objects.select_related("client").filter(
                    pk__in=[record.event_id for record in history.object_list]
                )
            }
            for record in history.object_list:
                record.related_event = events.get(record.event_id)
    return render(request, "quote_control/catalogue.html", {
        "form": form, "editing": entry,
        "product_rows": [x for x in all_entries if x.kind == "product"],
        "option_rows": [x for x in all_entries if x.kind == "option"],
        "pack_rows": [x for x in all_entries if x.kind == "pack"],
        "saved": request.GET.get("saved", "").isdigit(),
        "active_tab": active_tab,
        "auto_enabled": effective.enabled,
        "auto_offers_count": sum(
            1 for x in all_entries if x.kind in ("product", "pack")
            and x.active and x.auto_enabled
        ),
        "config": effective,
        "simulation_form": simulation_form,
        "simulation": simulation,
        "preview": preview,
        "preview_event": preview_event,
        "history": history,
        "sent_total": sent_total,
    })
