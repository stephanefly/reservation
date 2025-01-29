from time import sleep
from app.module.mail.send_mail_event import send_mail_event


def test_mail_devis(event):
    send_mail_event(event, 'devis')
    sleep(5)
    send_mail_event(event, 'rappel_devis')
    sleep(5)
    send_mail_event(event, 'last_rappel_devis')
    sleep(5)
    send_mail_event(event, 'prolongation_devis')
    sleep(5)
    send_mail_event(event, 'phonebooth_offert_devis')
    sleep(5)
    send_mail_event(event, 'last_chance_devis')