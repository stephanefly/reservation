"""Parametres effectifs : l'eligibilite se pilote UNIQUEMENT dans le Catalogue.

Les anciens interrupteurs sont conserves en base pour compatibilite,
mais ne conditionnent plus les nouvelles demandes : une offre active
et cochee suffit, sous reserve des regles strictes de tarification.
"""
from copy import copy

from .catalog import default_sources
from .models import AutoQuoteSettings, CatalogEntry


def has_automatic_offers():
    """Les options seules ne peuvent jamais activer l'envoi de devis."""
    return CatalogEntry.objects.filter(
        kind__in=("product", "pack"), active=True, auto_enabled=True,
    ).exists()


def effective_quote_config(config=None, *, automatic_offers=None):
    """Objet temporaire en lecture seule au sens metier : jamais sauvegarde.

    Le moteur continue de verifier toutes les regles (B2B, recommandation,
    option PDF, pack ambigu, duree, code postal, montant minimum).
    """
    result = copy(config) if config is not None else AutoQuoteSettings()
    if automatic_offers is None:
        automatic_offers = has_automatic_offers()
    result.enabled = bool(automatic_offers)
    result.catalog_enabled = True
    result.sources = default_sources()
    return result
