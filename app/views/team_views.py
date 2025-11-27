from django.views.decorators.http import require_http_methods
from ..models import EventTemplate, Event, EventRelance, TeamMember
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
import os
import json
from ..module.cloud.create_timelaps import upload_file_to_pcloud
from ..module.cloud.get_pcloud_data import get_pcloud_event_folder_data, upload_template_to_pcloud, \
    get_public_image_link_from_path
from ..module.mail.send_mail_event import send_mail_event
from django.template.loader import render_to_string

from ..module.team.team_calendar import get_event_statuses, build_event_data, get_stock_machines, get_stock_options, \
    group_events_by_date

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

    return render(request, 'app/team/team_post_presta.html',
                  {
                      'lst_post_event': lst_post_event,
                  })


def team_planning(request):
    today_minus_6h = today_date - timedelta(hours=6)

    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_minus_6h, end_week_date]
    ).order_by('event_details__date_evenement')

    team_members = TeamMember.objects.all()

    return render(request, 'app/team/team_planning.html',
                  {
                      'lst_event_prio': lst_event_prio,
                      'team_members': team_members,
                  })


@require_http_methods(["POST"])
def media_collected(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.event_post_presta.collected = True
    event.event_post_presta.save()
    return redirect('team_post_presta')


def calendar(request):
    # 1) Récupérer les événements bruts par statut
    event_statuses = get_event_statuses()

    # 2) Transformer en listes Python prêtes pour le JSON
    event_data = build_event_data(event_statuses)

    # 3) Récupérer les stocks
    stock_machines = get_stock_machines()
    stock_options = get_stock_options()

    # 4) Fusionner tous les événements pour le calcul par jour
    full_events = (
        event_data["events_ok_data"]
        + event_data["events_presta_fini_data"]
        + event_data["events_post_presta_data"]
    )

    # 5) Groupement par date + calcul des dispos machines/options
    grouped_by_date = group_events_by_date(
        full_events,
        stock_machines,
        stock_options
    )

    # 6) Envoi au template (ici seulement json.dumps pour JS)
    context = {
        # Pour colorer les jours dans le calendrier
        "events_ok_data": json.dumps(event_data["events_ok_data"]),
        "events_presta_fini_data": json.dumps(event_data["events_presta_fini_data"]),
        "events_post_presta_data": json.dumps(event_data["events_post_presta_data"]),

        # Pour afficher le détail du jour
        "calendar_data": json.dumps(grouped_by_date),
    }

    return render(request, "app/team/calendar.html", context)


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


