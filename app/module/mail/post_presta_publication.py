"""Notification interne de sélection des photos à publier (aucun envoi client)."""

from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid

from django.conf import settings

from app.models import EmailTracking
from app.module.cloud.get_pcloud_data import (
    get_pcloud_event_folder_data,
    get_pcloud_link_event_folder,
)
from app.module.mail.delivery import submit


MAIL_TYPE = "publication_a_poster"


def send_post_presta_publication_mail(event):
    """Envoie à Djordan un lien pCloud récent, sans modifier le lien client."""
    recipient = settings.POST_PRESTA_PUBLICATION_EMAIL
    if not recipient:
        raise ValueError("Adresse de notification Djordan non configurée.")

    # Ne jamais doubler un envoi dont le résultat SMTP est incertain.
    if EmailTracking.objects.filter(
        event_traced=event.id,
        mail_type=MAIL_TYPE,
        recipient__iexact=recipient,
        delivery_status="unknown",
    ).exists():
        raise ValueError(
            "Envoi précédent incertain : vérifier le journal des e-mails avant un renvoi."
        )

    folder_name = event.event_template.directory_name if event.event_template else None
    if not folder_name:
        raise ValueError("Nom du dossier pCloud absent pour cette prestation.")

    folder = get_pcloud_event_folder_data(folder_name)
    if not folder:
        raise ValueError("Dossier de photos introuvable sur pCloud.")

    # Le lien est créé au moment du mail : les liens clients existants peuvent expirer.
    link = get_pcloud_link_event_folder(folder)
    if not link or not link.startswith("https://"):
        raise ValueError("Lien de partage pCloud invalide.")

    event_date = (
        event.event_details.date_evenement.strftime("%d/%m/%Y")
        if event.event_details and event.event_details.date_evenement
        else "Non renseignée"
    )
    event_name = " ".join(str(event.client.nom).split())
    subject = f"[À PUBLIER] {event_name} - {event_date}"
    body = (
        "Bonjour Djordan,\n\n"
        "Cette prestation a été validée « À poster : Oui » dans le CRM MySelfieBooth.\n\n"
        f"Événement : {event_name}\n"
        f"Date : {event_date}\n"
        f"Dossier : {folder_name}\n"
        f"Photos pCloud : {link}\n\n"
        "Merci de sélectionner les meilleures photos, de préparer les publications "
        "Instagram, Facebook et LinkedIn selon leur pertinence, et de vérifier "
        "les autorisations de diffusion avant publication.\n"
        "Une fois les publications réalisées, mettre à jour « Posté » dans le CRM.\n\n"
        "MySelfieBooth\n"
    )

    delivery = EmailTracking.objects.create(
        event_traced=event.id,
        status_devis=event.status,
        recipient=recipient,
        mail_type=MAIL_TYPE,
        opening_tracked=False,
        delivery_status="preparing",
        message_id=make_msgid(domain=settings.MAIL_MYSELFIEBOOTH.rsplit("@", 1)[-1]),
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("MySelfieBooth", settings.MAIL_MYSELFIEBOOTH))
    msg["To"] = recipient
    return submit(delivery, msg)
