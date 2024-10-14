
from app.models import Event, EventPostPrestation
from django.utils import timezone
from datetime import datetime


# def maj_today_event():
#     events_before_today = Event.objects.filter(
#         event_details__date_evenement__lt=datetime.now(timezone.utc).date())
#
#     for event in events_before_today:
#         if event.signer_at:
#             event.status = "Post Presta"
#             post_presta = EventPostPrestation()
#             post_presta.save()  # On sauvegarde d'abord le post_presta avant de l'associer à l'event
#             event.post_presta = post_presta
#         else:
#             event.status = "Refused"
#         event.save()  # Ensuite, on sauvegarde l'event après avoir associé post_presta



def maj_today_event():
    # Définir la date du 20 septembre 2024
    start_date = datetime(2024, 9, 20).date()
    # Obtenir la date actuelle
    today = datetime.now(timezone.utc).date()

    # Filtrer les événements dont la date est entre le 20 septembre 2024 et aujourd'hui, avec le statut "Presta FINI" ou "Acompte OK"
    events_in_range = Event.objects.filter(
        event_details__date_evenement__range=(start_date, today),
        status__in=["Presta FINI", "Acompte OK"]
    )

    for event in events_in_range:
        if event.signer_at:
            event.status = "Post Presta"
            post_presta = EventPostPrestation()
            post_presta.save()  # On sauvegarde d'abord le post_presta avant de l'associer à l'event
            event.post_presta = post_presta
        else:
            event.status = "Refused"
        event.save()  # Ensuite, on sauvegarde l'event après avoir associé post_presta
