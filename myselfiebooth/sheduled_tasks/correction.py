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
from app.module.cloud.rennaming import normalize_name

lst_event_to_corriger = Event.objects.filter(status='Post Presta')

for event in lst_event_to_corriger:

    event.event_template.link_media_shared = str(event.event_template.directory_name)
    event.event_template.save()
    event.event_template.directory_name = normalize_name(event)
    event.event_template.save()
