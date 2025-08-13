import os
import sys
from datetime import datetime
from time import sleep

from app.module.mail.send_mail_event import send_mail_event

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

lst_event_to_relance = Event.objects.filter(
    status='Prolongation',
    client__autorisation_mail=True,
    signer_at__isnull=True,
    client__raison_sociale=False,
).order_by('created_at')

for event in lst_event_to_relance:
    send_mail_event(event, 'last_chance_devis')
    event.status = 'Last Chance'
    event.save()
    event.client.nb_relance_devis += 1
    event.client.save()
    sleep(20)
