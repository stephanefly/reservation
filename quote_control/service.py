"""Envoi des devis selon la configuration active, avec historique CRM."""

import logging

from django.db import DatabaseError

from .engine import analyse_quote
from .auto_policy import effective_quote_config, has_automatic_offers
from .models import AutoQuoteSettings, AutoQuoteLog

logger = logging.getLogger(__name__)


def process_instant_quote(event, send_mail):
    """Traitement sécurisé d'une nouvelle demande.

    La fonction n'intervient pas si aucune offre du catalogue n'est eligible.
    Aucun statut de réservation, paiement ou signature n'est validé.
    """
    try:
        # La case du Catalogue pilote les envois : aucun autre interrupteur.
        # Si la table n'est pas installee, les envois restent suspendus.
        if not has_automatic_offers():
            return False
        stored_config = AutoQuoteSettings.objects.filter(pk=1).first()
        config = effective_quote_config(stored_config, automatic_offers=True)
    except DatabaseError:
        logger.warning("Catalogue des devis indisponible ; envois suspendus.")
        return False

    source = (event.client.how_find or "").strip()
    try:
        analysis = analyse_quote(event, config)
        if not analysis["eligible"]:
            AutoQuoteLog.objects.create(
                event_id=event.pk, source=source,
                outcome="manual", reason=analysis["reason"],
            )
            return False

        for key, value in analysis["calculation"].items():
            setattr(event, key, value)
        event.status = "Calculed"
        event.save()

        delivered = send_mail(event, "devis")
        if not delivered:
            AutoQuoteLog.objects.create(
                event_id=event.pk, source=source, outcome="error",
                amount=analysis["amount"], reason="Mail non accepté : intervention nécessaire",
            )
            return False

        event.status = "Sended"
        event.save()
        AutoQuoteLog.objects.create(
            event_id=event.pk, source=source, outcome="sent",
            amount=analysis["amount"], reason=analysis["label"],
        )
        return True
    except Exception:
        logger.exception("Erreur devis automatique pour le dossier %s", event.pk)
        try:
            AutoQuoteLog.objects.create(
                event_id=event.pk, source=source, outcome="error",
                reason="Erreur technique : vérifier et envoyer manuellement",
            )
        except DatabaseError:
            logger.exception("Historique devis automatique indisponible")
        return False
