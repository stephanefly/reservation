"""Recorded SMTP submission. This module performs no automatic retries."""
import smtplib
from email.utils import make_msgid, formatdate

from django.conf import settings
from django.utils import timezone

from app.models import EmailDelivery


def begin_delivery(event, mail_type):
    recipient = event.client.mail.strip()
    if EmailDelivery.objects.filter(event=event, mail_type=mail_type, recipient__iexact=recipient, status="unknown").exists():
        raise ValueError("Un envoi précédent est incertain. Vérifier et résoudre son état avant de renvoyer ce type de mail.")
    domain = settings.MAIL_MYSELFIEBOOTH.rsplit("@", 1)[-1]
    return EmailDelivery.objects.create(event=event, recipient=recipient,
                                       mail_type=mail_type, message_id=make_msgid(domain=domain))


def finish(delivery, status, code=None, diagnostic=""):
    delivery.status = status
    delivery.smtp_code = code if isinstance(code, int) and 0 <= code <= 999 else None
    delivery.diagnostic = diagnostic[:500]
    delivery.save(update_fields=["status", "smtp_code", "diagnostic", "accepted_at", "copy_refused"])


def submit(delivery, message, copies=()):
    server = None
    submitting = False
    sender = settings.MAIL_MYSELFIEBOOTH
    recipients = list(dict.fromkeys([delivery.recipient] + [value.strip() for value in copies if value and value.strip()]))
    message["Message-ID"] = delivery.message_id
    if "Date" not in message:
        message["Date"] = formatdate(localtime=True)
    try:
        server = smtplib.SMTP_SSL("smtp.ionos.fr", 465, timeout=30)
        server.login(sender, settings.MP)
        serialized = message.as_string()
        options = {}
        if getattr(server, "has_extn", lambda name: False)("dsn"):
            options = {"mail_options": ["RET=HDRS"], "rcpt_options": ["NOTIFY=SUCCESS,FAILURE,DELAY"]}
        submitting = True
        refused = server.sendmail(sender, recipients, serialized, **options)
        # A BCC acceptance must never conceal a rejected client recipient.
        rejected_client = next((value for address, value in refused.items() if address.casefold() == delivery.recipient.casefold()), None)
        delivery.copy_refused = any(address.casefold() != delivery.recipient.casefold() for address in refused)
        if rejected_client:
            finish(delivery, "refused", rejected_client[0], "Le serveur SMTP a refusé le destinataire client.")
            raise smtplib.SMTPRecipientsRefused({delivery.recipient: rejected_client})
        delivery.accepted_at = timezone.now()
        finish(delivery, "accepted", diagnostic="Message accepté par IONOS pour le client ; réception finale non confirmée.")
        return True
    except smtplib.SMTPRecipientsRefused as exc:
        if delivery.status != "refused":
            codes = [value[0] for value in exc.recipients.values()]
            finish(delivery, "refused", codes[0] if codes else None, "Destinataire(s) refusé(s) par le serveur SMTP.")
        raise
    except smtplib.SMTPResponseException as exc:
        finish(delivery, "error", exc.smtp_code, "Erreur SMTP : authentification, expéditeur ou contenu refusé.")
        raise
    except (OSError, smtplib.SMTPException):
        finish(delivery, "unknown" if submitting else "error", diagnostic="Connexion interrompue pendant l'envoi ; ne pas relancer automatiquement." if submitting else "Connexion au serveur SMTP impossible.")
        raise
    except Exception:
        finish(delivery, "unknown" if submitting else "error", diagnostic="Résultat non confirmé ; vérifier le journal avant une nouvelle tentative.")
        raise
    finally:
        if server is not None:
            try:
                server.quit()
            except (OSError, smtplib.SMTPException):
                # QUIT failure after acceptance must not cause a duplicate send.
                try:
                    server.close()
                except (OSError, smtplib.SMTPException):
                    pass
