"""Ecran autonome du catalogue commercial, prive, sans ecriture dans app.Event."""
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .catalog_forms import CatalogEntryForm
from .models import CatalogEntry, AutoQuoteSettings


@staff_member_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def admin_catalog(request):
    identifier = request.POST.get("entry") if request.method == "POST" else request.GET.get("edit")
    identifier = (identifier or "").strip()
    if identifier and not identifier.isdigit():
        raise Http404("Identifiant de catalogue invalide")

    entry = get_object_or_404(CatalogEntry, pk=int(identifier)) if identifier else None
    form = CatalogEntryForm(request.POST if request.method == "POST" else None, instance=entry)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        return redirect(reverse("admin_catalog") + f"?saved={saved.pk}")

    all_entries = CatalogEntry.objects.all()
    config = AutoQuoteSettings.objects.filter(pk=1).first()
    return render(request, "quote_control/catalogue.html", {
        "form": form, "editing": entry,
        "product_rows": [x for x in all_entries if x.kind == "product"],
        "option_rows": [x for x in all_entries if x.kind == "option"],
        "pack_rows": [x for x in all_entries if x.kind == "pack"],
        "saved": request.GET.get("saved", "").isdigit(),
        "catalog_enabled": bool(config and config.catalog_enabled),
        "auto_enabled": bool(config and config.enabled),
    })
