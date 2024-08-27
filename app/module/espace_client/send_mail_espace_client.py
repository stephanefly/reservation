import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from bs4 import BeautifulSoup
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, MAIL_TEMPLATE_REPOSITORY, MAIL_COPIE, MAIL_BCC

def send_mail_espace_client(event, mail_type):
    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    # Définir les sujets et templates en fonction du type de mail
    if mail_type == 'validation':
        subject = "📸 Votre prestation est réservée : préparez-vous à vous éclater ! ✨"
        template_name = "mail_validation.html"
    elif mail_type == 'relance':
        subject = "📸 Informations manquantes pour votre événement ✨"
        template_name = "mail_relance_espace_client.html"
    elif mail_type == 'relance_avis':
        subject = "📸 Votre avis compte ! ✨"
        template_name = "mail_relance_avis.html"
    else:
        raise ValueError("Type de mail non reconnu. Utilisez 'validation' ou 'relance'.")

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
    soup_completed = complete_mail_content(event, soup, mail_type)

    # Attacher le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup_completed.prettify(), 'html'))

    # Envoi de l'e-mail
    server.sendmail(MAIL_MYSELFIEBOOTH, [msg['To']] + [MAIL_BCC], msg.as_string())

def complete_mail_content(event, soup, mail_type='validation'):
    # Complétion des champs communs
    soup.find('b', class_='client_nom').string = str(event.client.nom)
    soup.find('b', class_='date').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))

    # Ajout spécifique pour le mail de validation
    if mail_type == 'validation':
        selected_booths = event.event_product.get_selected_booths()
        prestation_tag = soup.find('b', class_='prestation')
        if prestation_tag:
            prestation_tag.string = selected_booths

    return soup
