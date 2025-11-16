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

def daily_event_integrity_check():
    # Exemple : tous les events "OK" mais avec des indices d'incomplet
    events_ok = Event.objects.filter(
        signer_at__isnull=False,
    )

    for event in events_ok:
        # On essaie de réparer automatiquement
        create_pcloud_event_folder(event)
        create_pcloud_event_folder(event, prepa=True)
        create_pcloud_event_folder(event, montage=True)
        create_notion_card(event)

if __name__ == "__main__":
    daily_event_integrity_check()