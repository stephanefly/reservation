import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup

from app.module.devis_pdf.generate_pdf import generate_devis_pdf
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, PDF_REPERTORY
from email.mime.application import MIMEApplication


def send_email(event):

    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    # Configuration de l'email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "MySelfieBooth - Votre devis - " + str(event.client)
    msg['From'] = MAIL_MYSELFIEBOOTH
    msg['To'] = event.client.mail

    # Corps de l'e-mail au format HTML
    # Ouvrir le fichier HTML en mode lecture (r pour read)
    with open(os.path.join(PDF_REPERTORY, "template_mail.html"), 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()
    soup = BeautifulSoup(html_message, 'html.parser')

    element_client = soup.find('a', class_='client_nom')
    element_client.string = str(event.client)
    element_client = soup.find('a', class_='date_event')
    element_client.string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))

    # Attachez le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup.prettify(), 'html'))

    buffer = generate_devis_pdf(event)

    # Attacher le PDF
    pdf_name = 'Devis-' +  str(event.client) + ".pdf"
    buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
    part = MIMEApplication(buffer.read(), Name=pdf_name)
    part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'

    msg.attach(part)

    server.sendmail(MAIL_MYSELFIEBOOTH,  str(event.client.mail), msg.as_string())

    return True
