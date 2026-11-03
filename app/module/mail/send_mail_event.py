import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from app.module.mail.complete_mail import complete_mail
from django.conf import settings


def send_mail_event(event, mail_type):
    from app.module.mail.delivery import begin_delivery, finish, submit

    delivery = begin_delivery(event, mail_type)
    try:
        subject, template_name, file_to_send, copy_mail = get_mail_template(event, mail_type)
        msg = MIMEMultipart('mixed' if file_to_send else 'alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr(("MySelfieBooth", settings.MAIL_MYSELFIEBOOTH))
        msg['To'] = delivery.recipient
        if copy_mail:
            msg['Cc'] = ",".join(copy_mail)
        template_path = os.path.join(settings.MAIL_TEMPLATE_REPOSITORY, template_name)
        with open(template_path, 'r', encoding='utf-8') as fichier_html:
            soup = BeautifulSoup(fichier_html.read(), 'html.parser')
        soup_completed = complete_mail(event, soup, mail_type)
        tracker = soup_completed.find('img', class_='traceur_devis')
        if tracker:
            from app.models import EmailTracking
            from urllib.parse import urlparse
            tracker_uuid = urlparse(tracker.get('src', '')).path.rstrip('/').rsplit('/', 1)[-1]
            tracking = EmailTracking.objects.filter(uuid=tracker_uuid, event_traced=event.id).first()
            delivery.tracking = tracking
            delivery.save(update_fields=['tracking'])
        msg.attach(MIMEText(soup_completed.prettify(), 'html'))
        if file_to_send:
            msg.attach(complete_mail_with_file_to_send(event, file_to_send))
    except Exception:
        finish(delivery, "error", diagnostic="Échec de préparation du message ; aucun envoi SMTP effectué.")
        raise
    result = submit(delivery, msg, copies=copy_mail + [settings.MAIL_BCC])
    if mail_type == 'send_media':
        event.event_post_presta.sent = True
        event.event_post_presta.save()
    elif mail_type == 'relance_avis':
        event.client.nb_relance_avis = (event.client.nb_relance_avis or 0) + 1
        event.client.save()
    return result

def complete_mail_with_file_to_send(event, file_to_send):

    # Si c'est un devis, générer et attacher le PDF
    if 'devis_file' in file_to_send:
        from app.module.data_bdd.post_form import make_num_devis
        from app.module.devis_pdf.generate_pdf import generate_pdf_devis
        if event.num_devis is None:
            make_num_devis(event)
        else:
            event.num_devis = event.num_devis + 1
            event.save()
        buffer = generate_pdf_devis(event)

        # Attacher le PDF
        pdf_name = 'Devis-' + str(event.client.nom) + "-" + str(event.num_devis) +".pdf"
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), _subtype='pdf', Name=pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'

    if 'template_file' in file_to_send:
        from app.module.cloud.get_pcloud_data import get_public_image_link_from_path
        full_path = r"/PREPA-EVENT/" + str(event.event_template.directory_name) + "/" + str(
            event.event_template.image_name)
        template_url = get_public_image_link_from_path(full_path)
        response = requests.get(template_url)
        file_name = event.event_template.image_name

        part = MIMEApplication(response.content, Name=file_name)
        part['Content-Disposition'] = f'attachment; filename="{file_name}"'

    return part



def send_mail_system_token_missing():
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(settings.MAIL_MYSELFIEBOOTH, settings.MP)

    subject = "Token manquant – action requise (generate_token.py)"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr(("MySelfieBooth", settings.MAIL_MYSELFIEBOOTH))
    msg['To'] = "contact@myselfiebooth-paris.fr"

    template_path = os.path.join(settings.MAIL_TEMPLATE_REPOSITORY, "system/mail_token_manquant.html")
    with open(template_path, 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_message = html_message.replace("{{DATE}}", date_str)

    msg.attach(MIMEText(html_message, 'html'))

    server.sendmail(settings.MAIL_MYSELFIEBOOTH, [msg['To']] + [settings.MAIL_BCC], msg.as_string())
    server.quit()

    return True

def get_mail_template(event, mail_type):

    file_to_send = []
    copy_mail = []

    # Mails nécessitant un devis
    if mail_type == 'devis':
        # Mail envoyé au client pour lui transmettre un devis personnalisé
        subject = "📸 Votre devis - " + str(event.client.nom) + " ✨"
        template_name = "devis/mail_devis.html"
        file_to_send.append('devis_file')

    elif mail_type == 'rappel_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Nous avons pensé à vous ! ✨"
        template_name = "devis/mail_first_rappel.html"
        file_to_send.append('devis_file')

    elif mail_type == 'last_rappel_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "⏳ Derniers jours pour en profiter! 📸"
        template_name = "devis/mail_last_rappel_devis.html"
        file_to_send.append('devis_file')

    elif mail_type == 'prolongation_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Nous prolongeons votre offre exceptionnelle ! ✨"
        template_name = "devis/mail_prolongation_devis.html"
        file_to_send.append('devis_file')

    elif mail_type == 'temoingnage_client_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Ils ont adoré ! Découvrez leur expérience ✨"
        template_name = "devis/mail_temoingnage_devis.html"
        file_to_send.append('devis_file')

    elif mail_type == 'phonebooth_offert_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Bonus exclusif : Phonebooth offert ! 🎁"
        template_name = "devis/mail_phonebooth_offert.html"
        file_to_send.append('devis_file')

    elif mail_type == 'last_chance_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Dernière chance : 50€ supplémentaires de remise ! ⚠️"
        template_name = "devis/mail_last_chance.html"
        file_to_send.append('devis_file')

# ---------------------------------------------------------------------------------------------------------------------
    # Mails ne nécessitant pas de devis
    elif mail_type == 'validation':
        # Mail de confirmation de réservation envoyé au client
        subject = "📸 Votre prestation est réservée : préparez-vous à vous éclater ! ✨"
        template_name = "clients/mail_validation.html"

    elif mail_type == 'relance_espace_client':
        # Mail pour relancer un client qui n'a pas complété les informations nécessaires dans son espace client
        subject = "📸 Informations manquantes pour votre événement ✨"
        template_name = "clients/mail_relance_espace_client.html"

    elif mail_type == 'send_media':
        # Mail pour envoyer les photos finales au client après l'événement
        subject = "📸 Vos photos sont là ! " + str(event.client.nom) + " ✨"
        template_name = "clients/mail_send_media.html"

    elif mail_type == 'relance_avis':
        # Mail pour demander au client de donner son avis sur la prestation
        subject = "📸 Votre avis compte ! ✨"
        template_name = "clients/mail_relance_avis.html"

    elif mail_type == 'envoi_template':
        # Mail pour envoyer le template au client
        subject = "📸 Votre Modèle est prêt ! ✨"
        template_name = "clients/mail_envoi_template.html"
        file_to_send.append('template_file')
        copy_mail.append("djordan.cartier@myselfiebooth-paris.fr")

    elif mail_type == 'token_manquant':
        subject = "Token manquant – action requise (generate_token.py)"
        template_name = "system/mail_token_manquant.html"

    else:
        # Lever une erreur si le type de mail fourni n'est pas reconnu
        raise ValueError("Type de mail non reconnu.")

    return subject, template_name, file_to_send, copy_mail


