"""Envoi des devis selon la configuration active, avec historique CRM."""

import logging

from django.db import DatabaseError

from .engine import analyse_quote, has_extra_options, selected_products, selected_options_summary
from .catalog import SOURCE_KEYS
from .auto_policy import effective_quote_config, has_automatic_offers
from .models import AutoQuoteSettings, AutoQuoteLog, CatalogEntry

logger = logging.getLogger(__name__)


def log_manual(event, reason):
    # Les codes et quantités réels sont conservés même si une option est gratuite.
    options = selected_options_summary(event)
    if options:
        suffix = " | Options : " + options
        reason = reason[:max(0, 255 - len(suffix))] + suffix
    AutoQuoteLog.objects.create(event_id=event.pk, source=(event.client.how_find or "").strip(),
                                outcome="manual", reason=reason[:255])


def final_automatic_guard(event, pack_code):
    """Dernier contrôle indépendant du calcul et des prix, sur la demande sauvegardée."""
    if event.client.raison_sociale or (event.client.how_find or "").strip().upper() not in SOURCE_KEYS:
        return False
    products = selected_products(event)
    if CatalogEntry.objects.filter(kind="product", code__in=products, active=True).count() != len(products):
        return False
    if pack_code:
        pack = CatalogEntry.objects.filter(code=pack_code, kind="pack", active=True,
                                           auto_enabled=True).first()
        return bool(pack and event.event_option.duree == 5
                    and set(pack.product_codes) == products
                    and not has_extra_options(event, pack.option_codes, pack.quantities))
    return (len(products) == 1 and event.event_option.duree in (3, 5) and not has_extra_options(event)
            and CatalogEntry.objects.filter(code__in=products, kind="product", active=True,
                                            auto_enabled=True).exists())


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
        # Recharger les relations sauvegardées, jamais uniquement le cache du formulaire.
        event.refresh_from_db()
        analysis = analyse_quote(event, config)
        if not analysis["eligible"]:
            log_manual(event, analysis["reason"])
            return False
        if not final_automatic_guard(event, analysis["pack"]):
            log_manual(event, "Composition ou offre incompatible : envoi automatique bloqué")
            return False

        for key, value in analysis["calculation"].items():
            setattr(event, key, value)
        event.status = "Calculed"
        event.save()

        event.refresh_from_db()
        if not final_automatic_guard(event, analysis["pack"]):
            log_manual(event, "Composition modifiée avant envoi : devis manuel obligatoire")
            return False
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
