import time

from app.models import Event
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from datetime import datetime, timedelta
from app.module.mail.send_mail_event import send_mail_event
from time import sleep

def process_events(days_offset, current_status, new_status, email_template, update_product=False, apply_discount=False):
    date_limite = datetime.now() - timedelta(days=days_offset)
    lst_event_to_relance = Event.objects.filter(
        client__autorisation_mail=True,
        created_at__date=date_limite.date(),
        signer_at__isnull=True,
        status=current_status,
        client__raison_sociale=False,
    ).order_by('created_at')

    for event in lst_event_to_relance:
        send_mail_event(event, email_template)
        event.status = new_status
        event.save()
        event.client.nb_relance_devis += 1
        event.client.save()
        sleep(20)


def choose_to_rappel_devis_client():
    process_events(2, 'Sended', 'First Rappel', 'rappel_devis')


def choose_to_last_rappel_devis_client():
    process_events(5, 'First Rappel', 'Last Rappel', 'last_rappel_devis')


def choose_to_prolonger_devis_client():
    process_events(8, 'Last Rappel', 'Prolongation', 'prolongation_devis')


def choose_to_temoignage_devis_client():
    process_events(10, 'Prolongation', 'Temoignage', 'temoingnage_client_devis')


def choose_to_phonebooth_offert_devis_client():
    process_events(12, 'Temoignage', 'Phonebooth Offert', 'phonebooth_offert_devis', update_product=True)


def choose_to_last_chance_devis_client():
    process_events(15, 'Phonebooth Offert', 'Last Chance', 'last_chance_devis', apply_discount=True)


def choose_to_relance_espace_client():
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
            time.sleep(30)  # Pause de 30 sec


def choose_to_make_review():
    some_days_ago = timezone.now().date() - relativedelta(days=2)

    # Utilise Q pour filtrer les événements qui ont lieu exactement dans une semaine ou dans un mois
    lst_event_to_make_review = Event.objects.filter(
        date_media_sent=some_days_ago,
        client__autorisation_mail=True,
        event_post_presta__feedback=False,
        status='Sent Media',
    )

    for event in lst_event_to_make_review:
        send_mail_event(event, 'relance_avis')
        time.sleep(30)  # Pause de 30 sec