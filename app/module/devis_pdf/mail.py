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
        server.login("contact@myselfiebooth-paris.fr", MP)

        # Configuration de l'email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Sujet de l'email"
        msg['From'] = "contact@myselfiebooth-paris.fr"
        msg['To'] = recipient_email

        # Corps de l'email
        html = f"""\
                <html>
                  <body>
                    <p>Cher {name},</p>
                    <p>Votre corps de l'email ici.</p>
                    <p>Cordialement,<br />Votre nom ici...</p>
                  </body>
                </html>
                """
        msg.attach(MIMEText(html, 'html'))

        buffer = generate_devis_pdf(event)

        # Attacher le PDF
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), Name="devis.pdf")
        part['Content-Disposition'] = 'attachment; filename="devis.pdf"'
        msg.attach(part)

        server.sendmail("contact@myselfiebooth-paris.fr", recipient_email, msg.as_string())


        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False
    finally:
        server.quit()
