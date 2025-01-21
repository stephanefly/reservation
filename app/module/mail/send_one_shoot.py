import time

from app.models import Event
from app.module.mail.send_mail_event import send_mail_event


def all_devis_send_one_shoot():
    lst_event = Event.objects.filter(
        client__raison_sociale=False,
        client__autorisation_mail=True,
        client__mail_sondage=False,
    )
    for event in lst_event:
        if event.client.mail_sondage == False:
            send_mail_event(event, "one_shoot")
            time.sleep(10)
            lst_client_mail = Event.objects.filter(client__mail=event.client.mail)
            for client in lst_client_mail:
                client.mail_sondage = True
                client.save()