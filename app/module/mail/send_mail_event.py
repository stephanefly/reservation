import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup

from app.module.data_bdd.post_form import make_num_devis
from app.module.devis_pdf.generate_pdf import generate_pdf_devis
from app.module.mail.complete_mail import complete_mail
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, MAIL_TEMPLATE_REPOSITORY, MAIL_COPIE, MAIL_BCC


def send_mail_event(event, mail_type):
    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    subject, template_name, need_devis = get_mail_template(event, mail_type)

    # Configuration de l'email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr(("MySelfieBooth", MAIL_MYSELFIEBOOTH))
    msg['Cc'] = MAIL_COPIE
    msg['To'] = event.client.mail

    # Lecture du template HTML
    template_path = os.path.join(MAIL_TEMPLATE_REPOSITORY, template_name)
    with open(template_path, 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()

    # Compléter le contenu du mail
    soup = BeautifulSoup(html_message, 'html.parser')
    soup_completed = complete_mail(event, soup, mail_type)

    # Attacher le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup_completed.prettify(), 'html'))

    # Si c'est un devis, générer et attacher le PDF
    if need_devis:
        if event.num_devis is None:
            make_num_devis(event)
        else:
            event.num_devis = event.num_devis + 1
            event.save()
        buffer = generate_pdf_devis(event)

        # Attacher le PDF
        pdf_name = 'Devis-' + str(event.client.nom) + "-" + str(event.num_devis) +".pdf"
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), Name=pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
        msg.attach(part)

    # Envoi de l'e-mail
    server.sendmail(MAIL_MYSELFIEBOOTH, [msg['To']] + [MAIL_BCC], msg.as_string())
    server.quit()  # Toujours fermer la connexion au serveur

    return True


def get_mail_template(event, mail_type):

    # Mails nécessitant un devis (need_devis = True)
    if mail_type == 'devis':
        # Mail envoyé au client pour lui transmettre un devis personnalisé
        subject = "📸 Votre devis - " + str(event.client.nom) + " ✨"
        template_name = "devis/mail_devis.html"
        need_devis = True

    elif mail_type == 'rappel_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Nous avons pensé à vous ! ✨"
        template_name = "devis/mail_first_rappel.html"
        need_devis = True

    elif mail_type == 'prolongation_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Nous prolongeons votre offre exceptionnelle ! ✨"
        template_name = "devis/mail_prolongation_devis.html"
        need_devis = True

    elif mail_type == 'phonebooth_offert_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Bonus exclusif : Phonebooth offert ! 🎁"
        template_name = "devis/mail_phonebooth_offert.html"
        need_devis = True

    elif mail_type == 'last_chance_devis':
        # Mail pour relancer un client concernant un devis envoyé précédemment
        subject = "📸 Dernière chance : 50€ supplémentaires de remise ! ⚠️"
        template_name = "devis/mail_last_chance.html"
        need_devis = True

# ---------------------------------------------------------------------------------------------------------------------
    # Mails ne nécessitant pas de devis (need_devis = False)
    elif mail_type == 'validation':
        # Mail de confirmation de réservation envoyé au client
        subject = "📸 Votre prestation est réservée : préparez-vous à vous éclater ! ✨"
        template_name = "mail_validation.html"
        need_devis = False

    elif mail_type == 'relance_espace_client':
        # Mail pour relancer un client qui n'a pas complété les informations nécessaires dans son espace client
        subject = "📸 Informations manquantes pour votre événement ✨"
        template_name = "mail_relance_espace_client.html"
        need_devis = False

    elif mail_type == 'send_media':
        # Mail pour envoyer les photos finales au client après l'événement
        subject = "📸 Vos photos sont là ! " + str(event.client.nom) + " ✨"
        template_name = "mail_send_media.html"
        need_devis = False
        # Marquer les médias comme envoyés dans la base de données
        event.event_post_presta.sent = True
        event.event_post_presta.save()

    elif mail_type == 'relance_avis':
        # Mail pour demander au client de donner son avis sur la prestation
        subject = "📸 Votre avis compte ! ✨"
        template_name = "mail_relance_avis.html"
        need_devis = False
        # Mise à jour du nombre de relances pour avis effectuées dans la base de données
        event.client.nb_relance_avis = event.client.nb_relance_avis + 1
        event.client.save()

    else:
        # Lever une erreur si le type de mail fourni n'est pas reconnu
        raise ValueError("Type de mail non reconnu.")

    return subject, template_name, need_devis

