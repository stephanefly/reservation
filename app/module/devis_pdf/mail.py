import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.module.devis_pdf.generate_pdf import generate_devis_pdf
from myselfiebooth.settings import MP
from email.mime.application import MIMEApplication


def send_email(event):

    try:

        name = "NomDuDestinataire"
        recipient_email = "faure_stephane@hotmail.fr"

        # Configuration du serveur SMTP
        server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
        server.login("stephane.faure@3dmouvstudio.com", MP)

        # Configuration de l'email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "MySelfieBooth - Votre devis - " + event.client
        msg['From'] = "stephane.faure@3dmouvstudio.com"
        msg['To'] = recipient_email

        # Corps de l'email
        html = r"img\template_mail.html"
        msg.attach(MIMEText(html, 'html'))

        buffer = generate_devis_pdf(event)

        # Attacher le PDF
        pdf_name = 'Devis-' + event.client + ".pdf"
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), Name=pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'

        msg.attach(part)

        server.sendmail("stephane.faure@3dmouvstudio.com", recipient_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False
    finally:
        server.quit()
