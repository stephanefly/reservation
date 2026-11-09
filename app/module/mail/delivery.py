"""Recorded SMTP submission. This module performs no automatic retries."""
import smtplib
import logging
from email.utils import make_msgid, formatdate, getaddresses

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from app.models import EmailTracking

logger = logging.getLogger(__name__)


def begin_delivery(event, mail_type):
    recipient = event.client.mail.strip()
    if EmailTracking.objects.filter(event_traced=event.id, mail_type=mail_type, recipient__iexact=recipient, delivery_status="unknown").exists():
        raise ValueError("Un envoi précédent est incertain. Vérifier et résoudre son état avant de renvoyer ce type de mail.")
    domain = settings.MAIL_MYSELFIEBOOTH.rsplit("@", 1)[-1]
    return EmailTracking.objects.create(event_traced=event.id, status_devis=event.status, opening_tracked=False, delivery_status="preparing", recipient=recipient,
                                       mail_type=mail_type, message_id=make_msgid(domain=domain))


def finish(delivery, status, code=None, diagnostic=""):
    previous = delivery.delivery_status
    delivery.delivery_status = status
    delivery.smtp_code = code if isinstance(code, int) and 0 <= code <= 999 else None
    delivery.diagnostic = diagnostic[:500]
    delivery.save(update_fields=["delivery_status", "smtp_code", "diagnostic", "accepted_at", "copy_refused"])
    if status in {"refused", "error", "unknown"} and previous != status:
        from app.module.mail.alerts import notify_failed_delivery
        transaction.on_commit(lambda tracking_id=delivery.pk: notify_failed_delivery(tracking_id))


def add_admin_cc(message, primary_recipient):
    """Ajoute la copie interne configurée en Cc, sans bloquer l'envoi client.

    Aucune adresse n'est choisie par défaut : confirmer l'adresse personnelle
    avant de configurer MAIL_ADMIN_CC dans settings.yaml.
    """
    email = str(getattr(settings, "MAIL_ADMIN_CC", "") or "").strip()
    if not email:
        return None
    try:
        if not email.isascii():
            raise ValidationError("Adresse non ASCII")
        validate_email(email)
    except ValidationError:
        logger.error("MAIL_ADMIN_CC invalide : copie ignorée.")
        return None

    if email.casefold() == str(primary_recipient).strip().casefold():
        return None

    existing = {
        address.casefold()
        for _, address in getaddresses(message.get_all("Cc", []))
    }
    if email.casefold() not in existing:
        if message.get("Cc"):
            message.replace_header("Cc", message["Cc"] + ", " + email)
        else:
            message["Cc"] = email
    return email


def submit(delivery, message, copies=()):
    server = None
    submitting = False
    sender = settings.MAIL_MYSELFIEBOOTH
    admin_cc = add_admin_cc(message, delivery.recipient)
    extra_recipients = [delivery.recipient] + [value.strip() for value in copies if value and value.strip()]
    if admin_cc:
        extra_recipients.append(admin_cc)
    # Dédupliquer aussi les adresses déjà dans un BCC ou Cc existant.
    recipients = list(dict.fromkeys(extra_recipients))
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
        if delivery.delivery_status != "refused":
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
