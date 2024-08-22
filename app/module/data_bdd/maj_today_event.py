
from app.models import Event
from datetime import timezone, datetime, timedelta

def maj_today_event():
    events_before_today = Event.objects.filter(
        event_details__date_evenement__lt=datetime.now(timezone.utc).date())
    for event in events_before_today:
        if event.signer_at:
            event.status = "Presta FINI"
        else:
            event.status = "Refused"
        event.save()
