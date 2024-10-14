
from app.models import Event, EventPostPrestation
from django.utils import timezone
from datetime import datetime


def maj_today_event():
    events_before_today = Event.objects.filter(
        event_details__date_evenement__lt=datetime.now(timezone.utc).date())

    for event in events_before_today:
        if event.signer_at:
            event.status = "Post Presta"
            post_presta = EventPostPrestation()
            post_presta.save()  # On sauvegarde d'abord le post_presta avant de l'associer à l'event
            event.post_presta = post_presta
        else:
            event.status = "Refused"
        event.save()  # Ensuite, on sauvegarde l'event après avoir associé post_presta
