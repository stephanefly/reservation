import os
import sys
from datetime import datetime
from time import sleep

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

lst_event_to_corriger = Event.objects.filter(
    status='Post Presta',
    )

for event in lst_event_to_corriger:
    if not hasattr(event, "event_post_presta") or event.event_post_presta is None:
        print(f"[INFO] Création d'un EventPostPrestation pour l'événement ID {event.id}")
        post_presta = EventPostPrestation()
        post_presta.save()
        print(f"[INFO] PostPresta ID {post_presta.id} créé")

        event.event_post_presta = post_presta
        event.save()
        print(f"[SUCCESS] Event ID {event.id} mis à jour avec PostPresta ID {post_presta.id}")
    else:
        print(f"[SKIP] Event ID {event.id} a déjà un EventPostPrestation associé (ID {event.event_post_presta.id})")

