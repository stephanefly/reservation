import os
import sys
import time


# Chemin absolu du répertoire parent de 'myselfiebooth'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Configurer Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myselfiebooth.settings")

import django
django.setup()

from myselfiebooth.settings import GOOGLE_TOKEN
from app.models import Event, EventPostPrestation
from app.module.cloud.get_pcloud_data import create_pcloud_event_folder
from app.module.notion.notion_service import create_notion_card
from app.module.google.contact import update_contact_keep_phone, test_service


def daily_event_integrity_check():

    events_ok = Event.objects.all()

    event_errors = {}

    try:
        test_service(GOOGLE_TOKEN)
        print("[OK] Google Contacts connecté")
    except Exception as e:
        print(f"[KO] Google Contacts connexion → {e}")

    def init_event_errors(event):
        if event.id not in event_errors:
            event_errors[event.id] = {
                "pcloud_client": False,
                "pcloud_prepa": False,
                "pcloud_montage": False,
                "notion": False,
                "google": False,
            }

    def mark_error(event, key, error):
        init_event_errors(event)
        event_errors[event.id][key] = True
        print(f"[KO] {key} → {error}")

    def ensure_post_presta(event):
        if event.event_post_presta is None:
            post_presta = EventPostPrestation.objects.create()
            event.event_post_presta = post_presta
            event.save(update_fields=["event_post_presta"])
            print("[OK] EventPostPrestation créé")

    def run_task(event, key, function):
        try:
            function()
            event_errors[event.id][key] = False
            print(f"[OK] {key}")
        except Exception as e:
            mark_error(event, key, e)

    print("\n========== PREMIER PASSAGE ==========")

    for event in events_ok:

        print(f"\n---- Event {event.id} (1er passage) ----")

        init_event_errors(event)
        ensure_post_presta(event)

        run_task(
            event,
            "pcloud_client",
            lambda: create_pcloud_event_folder(event)
        )

        run_task(
            event,
            "pcloud_prepa",
            lambda: create_pcloud_event_folder(event, prepa=True)
        )

        run_task(
            event,
            "pcloud_montage",
            lambda: create_pcloud_event_folder(event, montage=True)
        )

        run_task(
            event,
            "notion",
            lambda: create_notion_card(event)
        )

        run_task(
            event,
            "google",
            lambda: update_contact_keep_phone(event)
        )

    events_ko = [
        event_id
        for event_id, errors in event_errors.items()
        if any(errors.values())
    ]

    print("\n========== EVENTS KO APRÈS 1ER PASSAGE ==========")

    if not events_ko:
        print("Aucun event KO")
        return

    for event_id in events_ko:
        print(f"- Event {event_id} → {event_errors[event_id]}")

    print("\n========== DEUXIÈME PASSAGE ==========")

    for event_id in events_ko:

        event = Event.objects.get(id=event_id)
        errors = event_errors[event_id]

        print(f"\n---- Event {event.id} (2e passage) ----")

        ensure_post_presta(event)

        if errors.get("pcloud_client"):
            run_task(
                event,
                "pcloud_client",
                lambda: create_pcloud_event_folder(event)
            )

        if errors.get("pcloud_prepa"):
            run_task(
                event,
                "pcloud_prepa",
                lambda: create_pcloud_event_folder(event, prepa=True)
            )

        if errors.get("pcloud_montage"):
            run_task(
                event,
                "pcloud_montage",
                lambda: create_pcloud_event_folder(event, montage=True)
            )

        if errors.get("notion"):
            run_task(
                event,
                "notion",
                lambda: create_notion_card(event)
            )

        if errors.get("google"):
            time.sleep(2)
            run_task(
                event,
                "google",
                lambda: update_contact_keep_phone(event)
            )

    print("\n========== BILAN FINAL ==========")

    final_ko = [
        event_id
        for event_id, errors in event_errors.items()
        if any(errors.values())
    ]

    if not final_ko:
        print("Tous les events sont OK")
    else:
        for event_id in final_ko:
            print(f"[KO FINAL] Event {event_id} → {event_errors[event_id]}")


daily_event_integrity_check()