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


# Cartes historiques utilisées si le schéma de publication est indisponible.
_OPTION_DEFAULTS = {
    "MurFloral": (
        "Mur floral",
        "Décor photo premium pour obtenir un rendu plus chic sur les photos et vidéos.",
        "/static/img/allmur.jpg",
    ),
    "Phonebooth": (
        "Phonebooth audio",
        "Livre d’or audio rétro pour enregistrer les messages vocaux des invités.",
        "/static/img/phonebooth.jpg",
    ),
    "LivreOr": (
        "Livre d’or",
        "Support physique pour coller les tirages et conserver les messages des invités.",
        "/static/img/Livre-dor.jpg",
    ),
    "Fond360": (
        "Fond 360",
        "Fond lumineux pour améliorer le rendu visuel des vidéos 360 Booth.",
        "/static/img/fond360.jpg",
    ),
    "PanneauBienvenue": (
        "Panneau de bienvenue",
        "Panneau personnalisé pour guider les invités et renforcer la décoration.",
        "/static/img/Welcomeboard.jpg",
    ),
    "Holo3D": (
        "Hologramme 3D",
        "Animation visuelle originale pour donner un effet moderne à votre événement.",
        "/static/img/3dHolo.jpg",
    ),
    "PanneauFontaine": (
        "Panneau Fontaine",
        "Accueil élégant et visible pour l’entrée de salle, les mariages et les grands événements.",
        "/static/img/Panneau-fontaine.jpg",
    ),
    "VideoLivreOr": (
        "Livre d’or vidéo",
        "Capture de messages vidéo pour garder des souvenirs plus vivants et émotionnels.",
        "/static/img/livre-dor-video.jpg",
    ),
    "PhotographeVoguebooth": (
        "Photographe Vogue",
        "Photographe dédié pour obtenir des clichés plus propres et mieux cadrés.",
        "/static/img/photographe-voguebooth.jpg",
    ),
    "ImpressionVoguebooth": (
        "Impressions Vogue",
        "Ajout d’impressions instantanées pour offrir un souvenir physique aux invités.",
        "/static/img/impression-voguebooth.jpg",
    ),
    "DecorVoguebooth": (
        "Décor Vogue",
        "Décoration spécifique pour améliorer l’effet studio et l’expérience photo.",
        "/static/img/decoration-voguebooth.jpg",
    ),
    "PorteCles": (
        "Porte-clés photo",
        "Photo personnalisée intégrée dans un porte-clés souvenir à offrir aux invités.",
        "/static/img/PorteCles.png",
    ),
    "magnets": (
        "Magnets photo",
        "Support magnétique rigide avec photo intégrée et protection plastifiée.",
        "/static/img/magnets.png",
    ),
    "MagnetsSimple": (
        "Magnets simples",
        "Tirage photo classique avec magnet collé au dos. Simple, efficace et économique.",
        "/static/img/MagnetsSimple.png",
    ),
}

_XXL_OPTION = {
    "name": "Panneaux XXL",
    "description": "Panneaux photo personnalisés de 2 × 1 m, disponibles de 1 à 6.",
    "image_url": "/static/img/panneaux-xxl-cinema-duo.webp",
}


def _get_public_options():
    try:
        options = list(
            CatalogEntry.objects.filter(kind="option", active=True, public_enabled=True)
            .values("code", "name", "description", "image_url")
        )
    except DatabaseError:
        logger.warning("Publication des options indisponible : affichage du catalogue de repli")
        try:
            inactive_codes = set(
                CatalogEntry.objects.filter(kind="option", active=False)
                .values_list("code", flat=True)
            )
        except DatabaseError:
            inactive_codes = set()
        options = [
            {"code": code, "name": name, "description": description, "image_url": image}
            for code, (name, description, image) in _OPTION_DEFAULTS.items()
            if code not in inactive_codes
        ]

    for option in options:
        default = _OPTION_DEFAULTS.get(option["code"])
        if not option["image_url"] and default:
            option["image_url"] = default[2]

    # Les panneaux sont proposés par le formulaire, hors catalogue administrable.
    options.append(_XXL_OPTION.copy())
    return sorted(options, key=lambda option: option["name"].casefold())


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
        "public_options": _get_public_options(),
    }
