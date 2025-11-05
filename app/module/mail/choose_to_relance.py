import time

from app.models import Event
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from app.module.mail.send_mail_event import send_mail_event

from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from django.db.models import F

COOLDOWN_AFTER_STATUS_CHANGE = timedelta(days=1)  # empêche 2 mails le même jour

def _day_floor_n_days_ago(n: int):
    tz = timezone.get_current_timezone()
    target_date = (timezone.now() - timedelta(days=n)).date()
    return timezone.make_aware(datetime.combine(target_date, time.min), tz)

def process_events_until(min_days_ago: int, current_status: str, new_status: str, email_template: str):
    """
    Catch-up ouvert vers le passé (<= J-N) + 'one-step-per-run' (cooldown).
    Empêche l'envoi de 2 étapes le même jour lors d'un rattrapage massif.
    """
    batch_started_at = timezone.now()
    cutoff = _day_floor_n_days_ago(min_days_ago)
    cooldown_gate = batch_started_at - COOLDOWN_AFTER_STATUS_CHANGE

    # 1) On récupère uniquement les IDs pour limiter la mémoire
    ids = list(
        Event.objects
        .filter(
            client__autorisation_mail=True,
            signer_at__isnull=True,
            status=current_status,
            created_at__lt=cutoff,           # catch-up <= J-N
            updated_at__lt=cooldown_gate,    # évite double étape le même jour
        )
        .order_by('created_at')
        .values_list('pk', flat=True)
    )

    # 2) Traitement sûr par ligne
    for pk in ids:
        with transaction.atomic():
            try:
                evt = (
                    Event.objects
                    .select_related('client')
                    .select_for_update(skip_locked=True)
                    .get(pk=pk)
                )
            except Event.DoesNotExist:
                continue

            # Double-check en temps réel
            if (evt.status != current_status
                or evt.signer_at is not None
                or evt.created_at >= cutoff
                or evt.updated_at >= cooldown_gate):
                continue

            # Envoi
            send_mail_event(evt, email_template)

            # MAJ atomiques
            evt.status = new_status
            evt.save(update_fields=['status', 'updated_at'])

            evt.client.nb_relance_devis = F('nb_relance_devis') + 1
            evt.client.save(update_fields=['nb_relance_devis'])



# --- Raccourcis “catch-up” par étape ---
def choose_to_rappel_devis_client():
    process_events_until(2, 'Sended', 'First Rappel', 'rappel_devis')

def choose_to_last_rappel_devis_client():
    process_events_until(5, 'First Rappel', 'Last Rappel', 'last_rappel_devis')

def choose_to_prolonger_devis_client():
    process_events_until(8, 'Last Rappel', 'Prolongation', 'prolongation_devis')

def choose_to_last_chance_devis_client():
    process_events_until(14, 'Prolongation', 'Last Chance', 'last_chance_devis')


# def choose_to_temoignage_devis_client():
#     process_events_until(10, 'Prolongation', 'Temoignage', 'temoingnage_client_devis')
#
#
# def choose_to_phonebooth_offert_devis_client():
#     process_events_until(12, 'Temoignage', 'Phonebooth Offert', 'phonebooth_offert_devis')





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