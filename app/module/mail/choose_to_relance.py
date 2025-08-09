import time

from app.models import Event
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from datetime import datetime, timedelta
from app.module.mail.send_mail_event import send_mail_event
from time import sleep
# from app.module.mail.send_sms_event import send_sms_event


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

    # Liste des dates cibles
    target_dates = [
        now + relativedelta(days=4),
        now + relativedelta(weeks=1, days=3),
        now + relativedelta(weeks=2, days=2),
        now + relativedelta(weeks=3, days=1),
        now + relativedelta(months=1),
    ]

    # Récupération des événements correspondants
    lst_event_valid = (
        Event.objects.filter(
            Q(event_details__date_evenement__in=target_dates),
            status='Acompte OK'
        )
        .select_related('event_template', 'event_details', 'event_product')
    )

    for event_valid in lst_event_valid:
        # Vérifications obligatoires pour tous les événements
        if (
            event_valid.event_template is None
            or not event_valid.event_template.text_template
            or event_valid.event_details is None
            or not event_valid.event_details.horaire
        ):
            send_mail_event(event_valid, 'relance_espace_client')
            time.sleep(30)
            continue

        # Vérification spécifique si un design est nécessaire
        if event_valid.event_product.need_design() and not event_valid.event_template.url_modele:
            send_mail_event(event_valid, 'relance_espace_client')
            time.sleep(30)
            continue

        # Vérification spécifique si la musique est nécessaire
        if event_valid.event_product.need_music() and not event_valid.event_template.url_music_360:
            send_mail_event(event_valid, 'relance_espace_client')
            time.sleep(30)
            continue

        # Vérification spécifique si un mur floral est nécéssaire
        if event_valid.event_option.MurFloral and not event_valid.event_option.mur_floral_style:
            send_mail_event(event_valid, 'relance_espace_client')
            time.sleep(30)
            continue

def choose_to_make_review_mail():
    some_days_ago = timezone.now().date() - relativedelta(days=2)

    # Utilise Q pour filtrer les événements qui ont lieu exactement dans une semaine ou dans un mois
    lst_event_to_make_review = Event.objects.filter(
        date_media_sent=some_days_ago,
        client__autorisation_mail=True,
        event_post_presta__feedback_google=False,
        status='Sent Media',
    )

    for event in lst_event_to_make_review:
        send_mail_event(event, 'relance_avis')
        time.sleep(30)  # Pause de 30 sec

#
# def choose_to_make_review_sms():
#     some_days_ago = timezone.now().date() - relativedelta(days=4)
#
#     # Utilise Q pour filtrer les événements qui ont lieu exactement dans une semaine ou dans un mois
#     lst_event_to_make_review = Event.objects.filter(
#         date_media_sent=some_days_ago,
#         client__autorisation_mail=True,
#         event_post_presta__feedback=False,
#         status='Sent Media',
#     )
#
#     for event in lst_event_to_make_review:
#         send_sms_event(event, 'relance_avis')
#         time.sleep(30)  # Pause de 30 sec