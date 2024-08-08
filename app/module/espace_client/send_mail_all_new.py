import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from app.module.data_bdd.post_form import make_num_devis
from app.module.devis_pdf.generate_pdf import generate_pdf_devis
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, MAIL_TEMPLATE_REPOSITORY, MAIL_COPIE, MAIL_BCC
from email.mime.application import MIMEApplication

def send_email_espace_client(event):

    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    # Configuration de l'email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "📸 Découvrez notre tout nouvel espace client ! ✨"
    msg['From'] = formataddr(("MySelfieBooth", MAIL_MYSELFIEBOOTH))
    msg['Cc'] = MAIL_COPIE
    msg['To'] = event.client.mail

    # Corps de l'e-mail au format HTML
    # Ouvrir le fichier HTML en mode lecture (r pour read)
    with open(os.path.join(MAIL_TEMPLATE_REPOSITORY, "mail_ouverture_espace_client.html"), 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()
    soup = BeautifulSoup(html_message, 'html.parser')

    soup_completed = complete_mail_new_espace_client(event, soup)

    # Attachez le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup_completed.prettify(), 'html'))

    server.sendmail(MAIL_MYSELFIEBOOTH,  [msg['To']] + [MAIL_BCC], msg.as_string())

def complete_mail_new_espace_client(event, soup):

    soup.find('b', class_='client_nom').string = str(event.client.nom)
    soup.find('b', class_='date').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))

    return soup