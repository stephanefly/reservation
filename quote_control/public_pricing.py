"""Tarifs publics : catalogue CRM comme source, avec repli si migration absente.

La lecture n'active pas l'envoi des devis automatiques et ne modifie aucun devis.
Le tarif public 5h est celui du catalogue, independamment du mode devis auto.
Les tarifs 3h restent ceux du modele historique (non editables au catalogue).
"""
import logging

from django.db import DatabaseError

from app.module.data_bdd.price import PRIX_PRODUITS
from .catalog import PACKS, PRIX_VENTE_PAR_DEFAUT, PRODUCT_KEYS
from .models import CatalogEntry

logger = logging.getLogger(__name__)

_PACK_DEFAULTS = {code.replace("-", "_"): price for code, _, _, _, _, price in PACKS}
_KNOWN_PACK_KEYS = {pack[0] for pack in PACKS}


def get_public_catalogue():
    """Construire les valeurs de la page Tarifs et de la brochure à chaque requête.

    En absence de table (déploiement code avant migrate) ou panne MySQL,
    la vitrine ne doit pas planter. Les prix de repli sont les prix
    commerciaux connus du catalogue, pas les prix bruts des PDF.
    """
    prices = dict(PRIX_PRODUITS)
    prices.update(PRIX_VENTE_PAR_DEFAUT)
    packs = dict(_PACK_DEFAULTS)
    visibility = {code: True for code in PRODUCT_KEYS}
    visibility.update({code.replace("-", "_"): True for code in _KNOWN_PACK_KEYS})

    try:
        # Une seule requête ; aucun accès à AutoQuoteSettings ni écriture.
        rows = list(
            CatalogEntry.objects.filter(
                kind__in=("product", "pack"),
            ).values_list("kind", "code", "price", "active")
        )
    except DatabaseError:
        logger.warning("Catalogue tarifaire indisponible : prix de repli affichés")
        rows = []

    for kind, code, price, active in rows:
        if kind == "product" and code in PRODUCT_KEYS:
            visibility[code] = active
            if active:
                prices[code] = price
        elif kind == "pack" and code in _KNOWN_PACK_KEYS:
            key = code.replace("-", "_")
            visibility[key] = active
            if active:
                packs[key] = price

    # L'encart « Pack VIP » utilise le même pack Duo VIP, sans prix distinct.
    prices["pack"] = packs["duo_vip"]
    return {
        "data_price": prices,
        "pack_prices": packs,
        "public_active": visibility,
    }
