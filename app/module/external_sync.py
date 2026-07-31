import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections


logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="external-sync")


def _run_safely(sync_name, callback, *callback_args):
    close_old_connections()
    try:
        callback(*callback_args)
    except Exception:
        logger.exception("La synchronisation %s a échoué (arguments: %s)", sync_name, callback_args)
    finally:
        close_old_connections()


def _sync_trello_event(event_id):
    from app.models import Event
    from app.module.trello.get_trello_data import get_data_card_by_name
    from app.module.trello.update_data_card import (
        update_option_labels_trello,
        update_trello_date,
    )

    event = Event.objects.select_related(
        "client",
        "event_details",
        "event_option",
    ).get(pk=event_id)
    data_card = get_data_card_by_name(event.client.nom)
    if not data_card:
        logger.warning("Aucune carte Trello trouvée pour l'événement %s", event_id)
        return

    update_trello_date(event, data_card=data_card)
    update_option_labels_trello(event, data_card=data_card)


def _sync_google_contact(event_id):
    from app.models import Event
    from app.module.google.contact import update_contact_keep_phone

    event = Event.objects.select_related(
        "client",
        "event_details",
        "event_product",
        "event_template",
    ).get(pk=event_id)
    update_contact_keep_phone(event)


def _rename_pcloud_event_folders(old_directory_name, new_directory_name):
    from app.module.cloud.rennaming import rename_pcloud_event_folder

    rename_pcloud_event_folder(old_directory_name, new_directory_name, prepa=True)
    rename_pcloud_event_folder(old_directory_name, new_directory_name)


def queue_trello_sync(event_id):
    """Synchronise Trello sans bloquer la réponse HTTP de sauvegarde."""
    return _executor.submit(_run_safely, "Trello", _sync_trello_event, event_id)


def queue_google_contact_sync(event_id):
    """Synchronise Google Contacts sans bloquer la sauvegarde du modèle."""
    return _executor.submit(_run_safely, "Google Contacts", _sync_google_contact, event_id)


def queue_pcloud_rename(old_directory_name, new_directory_name):
    """Renomme les dossiers pCloud sans bloquer la sauvegarde."""
    return _executor.submit(
        _run_safely,
        "pCloud",
        _rename_pcloud_event_folders,
        old_directory_name,
        new_directory_name,
    )
