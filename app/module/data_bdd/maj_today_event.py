
from app.models import Event, EventPostPrestation
from django.utils import timezone
from datetime import datetime, timedelta


def maj_today_event():

    # Obtenir la date d'aujourd'hui
    today = datetime.now(timezone.utc).date()

    # Calculer la date d'hier
    yesterday = today - timedelta(days=1)

    # Filtrer les événements dont la date est exactement celle d'hier
    events_before_today = Event.objects.filter(
        event_details__date_evenement=yesterday
    )

    for event in events_before_today:
        if event.signer_at:
            event.status = "Post Presta"
            post_presta = EventPostPrestation()
            post_presta.save()  # On sauvegarde d'abord le post_presta avant de l'associer à l'event
            event.event_post_presta = post_presta
        else:
            event.status = "Refused"
        event.save()  # Ensuite, on sauvegarde l'event après avoir associé post_presta


