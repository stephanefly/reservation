import time

from app.models import Event
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Q

from app.module.mail.send_mail_event import send_mail_event


def choose_to_relance():
    # Calcul de la date actuelle, une semaine dans le futur, et un mois dans le futur
    now = timezone.now().date()
    some_days_later = now + relativedelta(days=4)
    one_week_later = now + relativedelta(weeks=1, days=3)
    two_week_later = now + relativedelta(weeks=2, days=2)
    three_week_later = now + relativedelta(weeks=3, days=1)
    one_month_later = now + relativedelta(months=1)

    # Utilise Q pour filtrer les événements qui ont lieu exactement dans une semaine ou dans un mois
    lst_event_valid = Event.objects.filter(
        Q(event_details__date_evenement=some_days_later) |
        Q(event_details__date_evenement=one_week_later) |
        Q(event_details__date_evenement=two_week_later) |
        Q(event_details__date_evenement=three_week_later) |
        Q(event_details__date_evenement=one_month_later),
        status='Acompte OK'
    ).select_related('event_template', 'event_details')

    for event_valid in lst_event_valid:
        # Vérifie si des informations essentielles sont manquantes pour l'événement
        if (event_valid.event_template is None or not event_valid.event_template.url_modele or not event_valid.event_template.text_template or
            event_valid.event_details is None or not event_valid.event_details.horaire):
            send_mail_event(event_valid, 'relance_espace_client')
            time.sleep(900)  # Pause de 15 minutes
