import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.module.devis_pdf.generate_pdf import generate_devis_pdf
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH
from email.mime.application import MIMEApplication


def send_email(event):

    try:
        # Configuration du serveur SMTP
        server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
        server.login(MAIL_MYSELFIEBOOTH, MP)

        # Configuration de l'email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "MySelfieBooth - Votre devis - " + str(event.client)
        msg['From'] = MAIL_MYSELFIEBOOTH
        msg['To'] = event.client.mail

        # Corps de l'email
        html = r"img\template_mail.html"
        msg.attach(MIMEText(html, 'html'))

        buffer = generate_devis_pdf(event)

        # Attacher le PDF
        pdf_name = 'Devis-' +  str(event.client) + ".pdf"
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), Name=pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'

        msg.attach(part)

        server.sendmail(MAIL_MYSELFIEBOOTH,  str(event.client.mail), msg.as_string())

        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False
    finally:
        server.quit()
