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

from app.models import Event
from app.module.mail.send_mail_event import send_mail_event

lst_event_to_corriger = Event.objects.filter(
    status='Sended',
    signer_at__isnull=True,
    client__autorisation_mail=True,
    )

for event in lst_event_to_corriger:

    if event.event_details.date_evenement < datetime.now().date():
        event.status = 'Refused'
        event.save()
    else :
        send_mail_event(event, 'last_rappel_devis')
        event.status = 'Last Rappel'
        event.save()
        event.client.nb_relance_devis += 1
        event.client.save()
        sleep(15)