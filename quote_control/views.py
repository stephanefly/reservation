"""Administration privée des devis automatiques et simulation PDF sans écriture."""

from copy import copy

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from app.models import Event
from app.module.devis_pdf.generate_pdf import generate_pdf_devis
from .engine import analyse_quote
from .models import AutoQuoteSettings


def event_queryset():
    return Event.objects.select_related(
        "client", "event_product", "event_option", "event_details",
    )


@staff_member_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def admin_quotes(request):
    """Ancienne URL : retour au Catalogue unique.

    Les POST de l'ancien formulaire sont redirigés sans changer les règles
    de calcul ou d'envoi, désormais pilotées par le catalogue.
    """
    if request.method == "POST":
        # Ancien formulaire retiré : ne jamais réactiver une configuration cachée.
        return redirect(reverse("admin_catalog") + "?tab=simulation")

    target = reverse("admin_catalog")
    query = request.GET.copy()
    query["tab"] = "simulation"
    return redirect(target + "?" + query.urlencode() + "#simulation")


@staff_member_required(login_url="/login/")
@require_GET
def preview_pdf(request, event_id):
    from .auto_policy import effective_quote_config

    config = effective_quote_config(AutoQuoteSettings.objects.filter(pk=1).first())
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
