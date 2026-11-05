"""Administration unique du Catalogue : offres, regles et simulation.

Le chemin historique /backend/devis-auto/ reste une route de compatibilite,
mais aucun second ecran ni second menu ne sont necessaires.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .catalog import PACKS, PRODUITS
from .catalog_forms import CatalogEntryForm
from .forms import QuoteControlForm
from .models import AutoQuoteLog, AutoQuoteSettings, CatalogEntry
from .price_breakdown import decorate_offers
from .simulation import QuoteSimulationForm


@staff_member_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def admin_catalog(request):
    """Une seule page, deux onglets internes. Aucune ecriture pour simuler."""
    config, _ = AutoQuoteSettings.objects.get_or_create(pk=1)
    legacy_settings_post = request.path.rstrip("/").endswith("/devis-auto")
    settings_post = request.method == "POST" and (
        request.POST.get("operation") == "settings" or legacy_settings_post
    )
    active_tab = "automation" if (
        settings_post or request.GET.get("tab") == "automation"
        or request.GET.get("simulate") == "1"
        or request.GET.get("event", "").isdigit()
    ) else "offres"

    # Ne jamais valider une offre lorsque l'utilisateur enregistre les regles
    # d'envoi ; les deux formulaires restent entierement independants.
    identifier = (request.POST.get("entry") if request.method == "POST" and not settings_post
                  else request.GET.get("edit")) or ""
    identifier = identifier.strip()
    if identifier and not identifier.isdigit():
        raise Http404("Identifiant de catalogue invalide")
    entry = get_object_or_404(CatalogEntry, pk=int(identifier)) if identifier else None

    form = CatalogEntryForm(
        request.POST if request.method == "POST" and not settings_post else None,
        instance=entry,
    )
    settings_form = QuoteControlForm(
        request.POST if settings_post else None,
        config=config,
    )

    if request.method == "POST":
        if settings_post and settings_form.is_valid():
            settings_form.save_to_config(config)
            return redirect(reverse("admin_catalog") + "?tab=automation&saved_settings=1#automation")
        if not settings_post and form.is_valid():
            saved = form.save()
            return redirect(reverse("admin_catalog") + f"?tab=offres&saved={saved.pk}#edition")

    simulation_form = QuoteSimulationForm(
        request.GET if request.GET.get("simulate") == "1" else None,
    )
    simulation = None
    if request.GET.get("simulate") == "1" and simulation_form.is_valid():
        simulation = simulation_form.simulate(config)

    # Conserver l'aperçu prive des anciens dossiers en lecture seule.
    preview = None
    preview_event = None
    event_id = (request.GET.get("event") or "").strip()
    if event_id.isdigit():
        from .engine import analyse_quote
        from .views import event_queryset
        preview_event = event_queryset().filter(pk=int(event_id)).first()
        preview = (analyse_quote(preview_event, config, preview=True)
                   if preview_event else {"eligible": False, "reason": "Devis introuvable"})

    all_entries = decorate_offers(CatalogEntry.objects.all())
    if entry is not None:
        entry.pricing = next(
            (x.pricing for x in all_entries if x.pk == entry.pk),
            {"available": False},
        )

    logs = list(AutoQuoteLog.objects.order_by("-created_at")[:40]) if active_tab == "automation" else []
    return render(request, "quote_control/catalogue.html", {
        "form": form, "editing": entry,
        "product_rows": [x for x in all_entries if x.kind == "product"],
        "option_rows": [x for x in all_entries if x.kind == "option"],
        "pack_rows": [x for x in all_entries if x.kind == "pack"],
        "saved": request.GET.get("saved", "").isdigit(),
        "saved_settings": request.GET.get("saved_settings") == "1",
        "catalog_enabled": config.catalog_enabled,
        "auto_enabled": config.enabled,
        "active_tab": active_tab,
        "config": config,
        "settings_form": settings_form,
        "auto_product_rows": [
            {"label": label, "field": settings_form["product_" + key]}
            for key, label in PRODUITS
        ],
        "auto_pack_rows": [
            {"label": pack[1], "field": settings_form["pack_" + pack[0]]}
            for pack in PACKS
        ],
        "simulation_form": simulation_form,
        "simulation": simulation,
        "preview": preview,
        "preview_event": preview_event,
        "logs": logs,
        "sent_count": AutoQuoteLog.objects.filter(outcome="sent").count()
            if active_tab == "automation" else 0,
        "manual_count": AutoQuoteLog.objects.filter(outcome="manual").count()
            if active_tab == "automation" else 0,
        "error_count": AutoQuoteLog.objects.filter(outcome="error").count()
            if active_tab == "automation" else 0,
    })
