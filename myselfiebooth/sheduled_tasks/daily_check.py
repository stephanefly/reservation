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

from app.models import Event
from app.module.cloud.get_pcloud_data import create_pcloud_event_folder
from app.module.trello.notion_service import create_notion_card
from app.module.google.contact import update_contact_keep_phone

def daily_event_integrity_check():
    # Exemple : tous les events "OK" mais avec des indices d'incomplet
    events_ok = Event.objects.filter(
        signer_at__isnull=False,
        status__in=["Acompte OK", "Post Presta", "Sent Media", "Media KO"],
    )

    event_ko = []
    for event in events_ok:

        # --- PCLOUD CLIENT ---
        try:
            create_pcloud_event_folder(event)
        except Exception as e:
            event_ko.append(event)
            print(f"[KO] pCloud (CLIENT) → {e}")

        # --- PCLOUD PREPA ---
        try:
            create_pcloud_event_folder(event, prepa=True)
        except Exception as e:
            event_ko.append(event)
            print(f"[KO] pCloud (PREPA) → {e}")

        # --- PCLOUD MONTAGE ---
        try:
            create_pcloud_event_folder(event, montage=True)
        except Exception as e:
            event_ko.append(event)
            print(f"[KO] pCloud (MONTAGE) → {e}")

        # --- NOTION ---
        try:
            create_notion_card(event)
        except Exception as e:
            event_ko.append(event)
            print(f"[KO] Notion → {e}")

        # --- GOOGLE CONTACTS ---
        try:
            update_contact_keep_phone(event)
        except Exception as e:
            event_ko.append(event)
            print(f"[KO] Google Contacts → {e}")

    print(f"Liste Event KO : {event_ko}")
    for event in event_ko:
        update_contact_keep_phone(event)

daily_event_integrity_check()