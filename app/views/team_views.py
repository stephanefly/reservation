from django.views.decorators.http import require_http_methods
from ..models import EventTemplate, Event, EventRelance
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import os

from ..module.data_bdd.make_planning import get_member_list
from ..module.cloud.connect_ftp_nas import SFTP_STORAGE

today_date = datetime.now().date()
from django.utils.timezone import now


def template_to_do(request):
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    return render(request, 'app/team/template_to_do.html', {
        'lst_event_prio': lst_event_prio,
    })


def change_status(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    event_template.statut = not event_template.statut
    event_template.save()
    return redirect('tableau_de_bord')


def upload_image(request, event_id):
    if request.method == 'POST':
        image = request.FILES.get('myTemplate')
        if image:
            # Sauvegarder l'image sur le NAS via SFTPStorage
            saved_path = SFTP_STORAGE._save_png(image, event_id)

            return redirect('template_to_do')

    return redirect('template_to_do')


def view_image(request, event_id):
    sftp_storage = SFTP_STORAGE  # Utilisez votre instance de connexion SFTP
    file_data, file_name = sftp_storage._get_last_image(event_id)  # Récupérer l'image

    # Détectez le type de contenu (vous pouvez ajuster selon votre fichier)
    content_type = "image/jpeg" if file_name.endswith(".jpg") or file_name.endswith(".jpeg") else "image/png"

    # Retourne l'image sans forcer le téléchargement
    response = HttpResponse(file_data, content_type=content_type)
    return response


def team_post_presta(request):
    lst_post_event = Event.objects.filter(
        signer_at__isnull=False,
        status='Post Presta'
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_post_event)

    return render(request, 'app/team/team_post_presta.html',
                  {
                      'lst_post_event': lst_post_event,
                      'event_lst_member': event_lst_member
                  })


def team_planning(request):
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_event_prio)
    print(event_lst_member)

    return render(request, 'app/team/team_planning.html',
                  {
                      'lst_event_prio': lst_event_prio,
                      'event_lst_member': event_lst_member
                  })


@require_http_methods(["POST"])
def media_collected(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.event_post_presta.collected = True
    event.event_post_presta.save()
    return redirect('team_post_presta')


def transform_event_data(events):
    """
    Transforme une liste d'événements en une structure JSON.
    """
    return [
        {
            "date": e.event_details.date_evenement.strftime('%Y-%m-%d'),
            "title": e.client.nom,
            "product": e.event_product.get_selected_booths(),
            "ville": e.event_details.ville_evenement,
            "code_postal": str(e.event_details.code_postal_evenement)[:2],
        }
        for e in events
    ]


def calendar(request):
    # Récupération des événements par statut
    event_statuses = {
        "events_ok_data": Event.objects.filter(status="Acompte OK"),
        "events_presta_fini_data": Event.objects.filter(status="Presta FINI"),
        "events_post_presta_data": Event.objects.filter(status="Post Presta"),
        "events_devis_en_cours_data": Event.objects.exclude(status__in=[
            "Acompte OK", "Presta FINI", "Post Presta", "Refused"]),
    }

    # Transformation des données pour l'affichage
    event_data = {
        key: transform_event_data(value)
        for key, value in event_statuses.items()
    }
    print(event_data['events_presta_fini_data'])
    return render(request, 'app/team/calendar.html', event_data)


def relance_client(request):
    event_to_relance = Event.objects.filter(
        status__in=["Prolongation", "Last Chance", "Last Rappel", "Initied"]
    ).select_related("event_details").order_by("event_details__date_evenement")

    return render(request, 'app/team/relance_appel_client.html', {'event_to_relance': event_to_relance})


def info_relance_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    lst_relance_event = EventRelance.objects.filter(event=event).order_by('date_relance')
    event_reduc_total = event.reduc_all + event.reduc_product

    if request.method == "POST":
        membre = request.POST.get("membre")
        date_relance = request.POST.get("date_relance")
        commentaire = request.POST.get("commentaire")
        qualification = int(request.POST.get("qualification", 0))

        # Création de la relance
        EventRelance.objects.create(
            event=event,
            membre=membre,
            date_relance=date_relance if date_relance else now(),
            commentaire=commentaire,
            qualification=qualification,
        )

        return redirect("info_relance_client", event_id=event.id)  # Rafraîchir la page après l'ajout

    return render(request, "app/team/info_relance_client.html",
                  {"event": event, "lst_relance_event": lst_relance_event,  "now": now(),"event_reduc_total":event_reduc_total})
