
from app.models import Event, EventPostPrestation
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from app.module.cloud.get_pcloud_data import get_pcloud_event_folder_data, create_pcloud_event_folder
from app.module.cloud.share_link import create_link_event_folder


def maj_today_event():

    # Obtenir la date d'aujourd'hui
    today = datetime.now(timezone.utc).date()

    # Calculer la date d'hier
    yesterday = today - timedelta(days=1)

    # Filtrer les événements dont la date est hier ou antérieure
    events_yesterday = Event.objects.filter(
        event_details__date_evenement=yesterday,
    )

    for event in events_yesterday:
        if event.signer_at:
            event.status = "Post Presta"
            post_presta = EventPostPrestation()
            post_presta.save()  # On sauvegarde d'abord le post_presta avant de l'associer à l'event
            event.event_post_presta = post_presta

            if not get_pcloud_event_folder_data(event.event_template.directory_name):
                create_pcloud_event_folder(event)

            # On créer le lien de téléchargement
            create_link_event_folder(event)

        else:
            event.status = "Refused"
        event.save()  # Ensuite, on sauvegarde l'event après avoir associé post_presta
