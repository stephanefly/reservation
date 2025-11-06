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
from app.module.google.contact import create_google_contact
from time import sleep

events = Event.objects.order_by("-created_at")

seen = set()
unique_events = []

for event in events:
    phone = event.client.numero_telephone
    if phone not in seen:
        seen.add(phone)
        unique_events.append(event)

print(f"{len(unique_events)} contacts à créer.")

for i, event in enumerate(unique_events, 1):
    print(f"{i}/{len(unique_events)} - {event.client.nom}")
    create_google_contact(event)
    sleep(1)