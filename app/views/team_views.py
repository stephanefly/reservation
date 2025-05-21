from django.views.decorators.http import require_http_methods
from ..models import EventTemplate, Event, EventRelance
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
import os

from ..module.cloud.create_timelaps import upload_file_to_pcloud
from ..module.cloud.get_pcloud_data import get_pcloud_event_folder_data
from ..module.cloud.share_link import upload_template_to_pcloud, get_public_image_link_from_path
from ..module.data_bdd.make_planning import get_member_list
from ..module.mail.send_mail_event import send_mail_event

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
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        image = request.FILES.get('myTemplate')
        if image:
            # Sauvegarder l'image sur le NAS via SFTPStorage
            folder_data = get_pcloud_event_folder_data(event.event_template.directory_name, prepa=True)
            upload_template_to_pcloud(event, image, folder_data)

            return redirect('template_to_do')

    return redirect('template_to_do')

def send_template_to_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_event(event, 'envoi_template')
    return redirect('template_to_do')

def view_image(request, event_id):
    event = Event.objects.get(id=event_id)
    full_path = r"/PREPA-EVENT/" + str(event.event_template.directory_name) + "/" + str(event.event_template.image_name)
    template_url = get_public_image_link_from_path(full_path)
    return HttpResponseRedirect(template_url)


def team_post_presta(request):
    lst_post_event = Event.objects.filter(
        signer_at__isnull=False,
        status__in=['Post Presta']
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_post_event)

    return render(request, 'app/team/team_post_presta.html',
                  {
                      'lst_post_event': lst_post_event,
                      'event_lst_member': event_lst_member
                  })


def team_planning(request):
    today_minus_6h = today_date - timedelta(hours=6)

    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_minus_6h, end_week_date]
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
