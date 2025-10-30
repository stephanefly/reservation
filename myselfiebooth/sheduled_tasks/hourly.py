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
from app.module.cloud.send_media import send_media_logic

events = Event.objects.filter(status='Pending')

for event in events:
    try:
        send_media_logic(event.id)
        event.status = "Sent Media"
        event.save(update_fields=["status"])
    except Exception as e:
        event.status = "Media KO"
        event.save(update_fields=["status"])