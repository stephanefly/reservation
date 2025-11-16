import os
import sys

# Chemin absolu du répertoire parent de 'myselfiebooth'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Maintenant, vous pouvez importer 'myselfiebooth'

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myselfiebooth.settings')
import django

django.setup()

from app.models import Event, EventPostPrestation
from app.module.cloud.get_pcloud_data import create_pcloud_event_folder
from app.module.trello.notion_service import create_notion_card
from app.module.google.contact import update_contact_keep_phone

def daily_event_integrity_check():
    # Exemple : tous les events "OK" mais avec des indices d'incomplet
    # events_ok = Event.objects.filter(
    #     signer_at__isnull=False,
    #     status__in=["Acompte OK", "Post Presta", "Sent Media", "Media KO"],
    # )

    events_ok = Event.objects.filter(pk__in=[2766])

    event_errors = {}  # event_id → dict des KO

    def mark_error(event, key):
        """Marque une fonction comme KO pour un event."""
        if event.id not in event_errors:
            event_errors[event.id] = {}
        event_errors[event.id][key] = True

    # ========= PREMIER PASSAGE =========
    for event in events_ok:

        print(f"\n---- Event {event.id} (1er passage) ----")
        event_errors.setdefault(event.id, {})  # structure prête

        if event.event_post_presta is None:
            post_presta = EventPostPrestation.objects.create()  # juste ça
            event.event_post_presta = post_presta
            event.save(update_fields=["event_post_presta"])

        # --- PCLOUD CLIENT ---
        try:
            create_pcloud_event_folder(event)
            event_errors[event.id]["pcloud_client"] = False
        except Exception as e:
            print(f"[KO] pCloud (CLIENT) → {e}")
            mark_error(event, "pcloud_client")

        # --- PCLOUD PREPA ---
        try:
            create_pcloud_event_folder(event, prepa=True)
            event_errors[event.id]["pcloud_prepa"] = False
        except Exception as e:
            print(f"[KO] pCloud (PREPA) → {e}")
            mark_error(event, "pcloud_prepa")

        # --- PCLOUD MONTAGE ---
        try:
            create_pcloud_event_folder(event, montage=True)
            event_errors[event.id]["pcloud_montage"] = False
        except Exception as e:
            print(f"[KO] pCloud (MONTAGE) → {e}")
            mark_error(event, "pcloud_montage")

        # --- NOTION ---
        try:
            create_notion_card(event)
            event_errors[event.id]["notion"] = False
        except Exception as e:
            print(f"[KO] Notion → {e}")
            mark_error(event, "notion")

        # --- GOOGLE CONTACTS ---
        try:
            update_contact_keep_phone(event)
            event_errors[event.id]["google"] = False
        except Exception as e:
            print(f"[KO] Google Contacts → {e}")
            mark_error(event, "google")

    # ========= LISTE DES EVENTS KO =========
    print("\n==== Events KO après 1er passage ====")
    events_ko = [eid for eid, errs in event_errors.items() if any(errs.values())]

    for eid in events_ko:
        print(f"- Event {eid}")

    for event_id in events_ko:
        event = Event.objects.get(id=event_id)
        print(f"\n---- Event {event.id} (2e passage) ----")

        errs = event_errors[event_id]

        if errs.get("pcloud_client"):
            create_pcloud_event_folder(event)
            print("[DONE] pCloud CLIENT")

        if errs.get("pcloud_prepa"):
            create_pcloud_event_folder(event, prepa=True)
            print("[DONE] pCloud PREPA")

        if errs.get("pcloud_montage"):
            create_pcloud_event_folder(event, montage=True)
            print("[DONE] pCloud MONTAGE")

        if errs.get("notion"):
            create_notion_card(event)
            print("[DONE] Notion")

        if errs.get("google"):
            update_contact_keep_phone(event)
            print("[DONE] Google Contacts")


daily_event_integrity_check()