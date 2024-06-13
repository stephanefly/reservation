import json
import os
from datetime import timezone, datetime, timedelta
import requests
from django.template.loader import render_to_string

from app.models import Event
from myselfiebooth.settings import TOKEN_TRELLO, KEY_TRELLO


def maj_today_event():
    events_before_today = Event.objects.filter(
        event_details__date_evenement__lt=datetime.now(timezone.utc).date())
    for event in events_before_today:
        if event.signer_at:
            event.status = "Presta FINI"
        else:
            event.status = "Refused"
        event.save()


def create_html_planning():
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=10)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    # Générer le contenu HTML à partir d'un modèle
    context = {'lst_event_prio': lst_event_prio}
    html_content = render_to_string('app/backend/planning.html', context)

    file_path = r"app/planning.html"
    with open(file_path, 'w') as f:
        f.write(html_content)

    return file_path


def attach_html_planning(file_path, id_card_plannif):

    url = f"https://api.trello.com/1/cards/{id_card_plannif}/attachments"

    with open(file_path, 'rb') as file:
        query = {
            'key': KEY_TRELLO,
            'token': TOKEN_TRELLO,
            'name': 'PLANNING.html'
        }

        response = requests.post(
            url,
            params=query,
            files={'file': file}
        )


def get_and_delete_attachement(id_card_plannif):

    query = {
        'key': KEY_TRELLO,
        'token': TOKEN_TRELLO,
    }
    # URL de l'API pour obtenir les pièces jointes
    url = f"https://api.trello.com/1/cards/{id_card_plannif}/attachments"

    response = requests.get(
        url,
        params=query
    )

    attachments = json.loads(response.text)

    if attachments:
        # URL de l'API pour supprimer une pièce jointe
        url = f"https://api.trello.com/1/cards/{id_card_plannif}/attachments/{attachments[0]['id']}"

        requests.delete(
            url,
            params=query
        )


def make_planning():

    # Paramètres pour créer une carte
    id_card_plannif = "666849763ceda7f88c19f0b6"

    file_path = create_html_planning()

    get_and_delete_attachement(id_card_plannif)

    attach_html_planning(file_path, id_card_plannif)


