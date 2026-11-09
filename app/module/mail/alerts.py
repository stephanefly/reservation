"""Alertes internes CRM. Aucune relance automatique n'est envoyée au client."""
import logging
import smtplib
from email.message import EmailMessage

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

logger = logging.getLogger(__name__)


def send_admin_alert(subject, body):
    """Alerter le responsable sans déclencher le moteur d'envoi client.

    La remise finale à la boîte du responsable reste à surveiller : IONOS
    n'accuse réception que de la soumission SMTP.
    """
    sender = str(getattr(settings, "MAIL_MYSELFIEBOOTH", "") or "").strip()
    recipient = str(getattr(settings, "CRM_ALERT_EMAIL", "") or
                    getattr(settings, "MAIL_ADMIN_CC", "") or "").strip()
    try:
        if not sender or not recipient or not recipient.isascii():
            raise ValidationError("Configuration d'alerte absente ou invalide.")
        validate_email(sender)
        validate_email(recipient)
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP_SSL("smtp.ionos.fr", 465, timeout=20) as server:
            server.login(sender, settings.MP)
            refused = server.sendmail(sender, [recipient], message.as_string())
            if refused:
                logger.error("Alerte CRM refusée par le serveur SMTP.")
                return False
        return True
    except (ValidationError, OSError, smtplib.SMTPException, Exception):
        # Ne jamais faire échouer la demande client pour une alerte interne.
        logger.exception("Alerte CRM indisponible : consulter le tableau de suivi.")
        return False


def notify_failed_delivery(tracking_id):
    """Notification ponctuelle après un nouveau refus ou retour de livraison."""
    from app.models import EmailTracking, Event

    delivery = EmailTracking.objects.filter(pk=tracking_id).first()
    if delivery is None or delivery.delivery_status not in (
            "bounced", "refused", "error", "unknown", "delayed"):
        return False
    event = Event.objects.select_related("client").filter(pk=delivery.event_traced).first()
    dossier = str(delivery.event_traced or "indéfini")
    client = event.client.nom if event else "Client inconnu"
    url = f"https://reservation.myselfiebooth-paris.fr/backend/info-event/{dossier}/"
    body = (
        f"Incident de livraison MySelfieBooth\n\n"
        f"Dossier : #{dossier}\nClient : {client}\n"
        f"Destinataire : {delivery.recipient}\n"
        f"Type de mail : {delivery.mail_type}\n"
        f"État technique : {delivery.get_delivery_status_display()}\n"
        f"Code SMTP : {delivery.smtp_code or 'non communiqué'}\n"
        f"Diagnostic : {delivery.diagnostic}\n\n"
        f"Vérifier le dossier : {url}\n"
        "Ne pas renvoyer automatiquement : contacter le client par un autre canal."
    )
    return send_admin_alert(f"[ALERTE CRM] Mail non livré - dossier #{dossier}", body)
