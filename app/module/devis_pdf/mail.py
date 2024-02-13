import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
from datetime import datetime, timedelta


from app.module.devis_pdf.generate_pdf import generate_devis_pdf
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, PDF_REPERTORY, MAIL_COPIE, MAIL_BCC
from email.mime.application import MIMEApplication


def send_email(event):

    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    # Configuration de l'email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "MySelfieBooth - Votre devis - " + str(event.client.nom)
    msg['From'] = MAIL_MYSELFIEBOOTH
    msg['Cc'] = MAIL_COPIE
    msg['To'] = event.client.mail

    # Corps de l'e-mail au format HTML
    # Ouvrir le fichier HTML en mode lecture (r pour read)
    with open(os.path.join(PDF_REPERTORY, "template_mail.html"), 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()
    soup = BeautifulSoup(html_message, 'html.parser')

    soup_completed = complete_mail(event, soup)

    # Attachez le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup_completed.prettify(), 'html'))

    buffer = generate_devis_pdf(event)

    # Attacher le PDF
    pdf_name = 'Devis-' +  str(event.client.nom) + ".pdf"
    buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
    part = MIMEApplication(buffer.read(), Name=pdf_name)
    part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'

    msg.attach(part)

    server.sendmail(MAIL_MYSELFIEBOOTH,  [msg['To']] + [MAIL_BCC], msg.as_string())

    return True


def complete_mail(event, soup):

    soup.find('a', class_='client_nom').string = str(event.client)
    soup.find('a', class_='date_event').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))

    if event.prix_brut > event.prix_proposed:
        soup.find('a', class_='txt_reduc').string = " et bénéficier de la reservation"

    if event.prix_proposed >= 600:
        soup.find('a', class_='acompte').string = "100 €"
    elif event.prix_proposed >= 1000:
        soup.find('a', class_='acompte').string = "150 €"
    else:
        soup.find('a', class_='acompte').string = "50 €"

    # Ajouter 10 jours à la date de l'événement
    date_j_plus_10 = datetime.now() + timedelta(days=8)
    soup.find('a', class_='date_butoire').string = date_j_plus_10.strftime('%d/%m/%Y')

    return soup