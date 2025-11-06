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

lst_events_contact = (
    Event.objects
    .order_by("client__numero_telephone", "-created_at")
    .distinct("client__numero_telephone")
)
total = lst_events_contact.count()
print(f"{total} contacts à créer.\n")

for index, event in enumerate(lst_events_contact, start=1):
    print(f"{index} / {total} → Création Google Contact → {event.client.nom}")
    create_google_contact(event)
    sleep(1)