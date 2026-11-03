"""Email dashboard in the authenticated CRM; no private token in the browser."""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from app.models import Event
from app.views.private_api_data import email_report


STATUS_LABELS = dict(Event.STATUS, Sended="Devis envoyé", Resended="Devis renvoyé",
                     **{"First Rappel": "Première relance", "Last Rappel": "Dernière relance",
                        "Last Chance": "Dernière offre", "Prolongation": "Prolongation",
                        "Temoignage": "Témoignage", "Phonebooth Offert": "Phonebooth offert"})


@never_cache
@staff_member_required(login_url="login")
@require_GET
def graph_email_stats(request):
    context = {"start_date": request.GET.get("start_date", ""),
               "end_date": request.GET.get("end_date", "")}
    try:
        report = email_report(request)
    except ValueError as exc:
        context["error"] = str(exc)
        return render(request, "app/backend/graph/graph_email_stats.html", context, status=400)
    for row in report["by_status"]:
        row["label"] = STATUS_LABELS.get(row["status_devis"], row["status_devis"] or "Statut non renseigné")
    context.update(report)
    return render(request, "app/backend/graph/graph_email_stats.html", context)
