"""Catalogue commercial pour le pilotage des devis automatiques.

Une offre pack est reconnue seulement pour sa combinaison exacte de machines,
avec toutes les options incluses. Les autres combinaisons restent manuelles.
"""

SOURCES = (
    ("INSTAGRAM", "Instagram"),
    ("LINKEDIN", "LinkedIn"),
    ("SITE INTERNET", "Site internet"),
    ("LEBONCOIN", "Leboncoin"),
)

PRODUITS = (
    ("photobooth", "Photobooth"),
    ("miroirbooth", "Miroirbooth"),
    ("videobooth", "360 Booth"),
    ("voguebooth", "Vogue Booth"),
    ("airbooth", "360 Airbooth"),
    ("ipadbooth", "iPad Booth"),
)

# Prix TTC commerciaux à durée standard. Le PDF conserve les tarifs bruts du
# CRM et matérialise l'éventuelle différence en remise produit.
PRIX_VENTE_PAR_DEFAUT = {
    "photobooth": 400,
    "miroirbooth": 500,
    "videobooth": 450,
    "voguebooth": 550,
    "airbooth": 450,
    "ipadbooth": 250,
}

# (Identifiant, nom, machines, options requises, quantités minimales, tarif TTC).
# Les frais de livraison hors zones incluses et les options supplémentaires
# restent en supplément.
PACKS = (
    ("souvenirs", "Pack Souvenirs", ("photobooth",),
     ("Phonebooth",), (("PorteCles", 100),), 600),
    ("immersion-360", "Pack Immersion 360", ("videobooth",),
     ("VideoLivreOr", "Fond360"), (), 700),
    ("signature", "Pack Signature", ("miroirbooth",),
     ("VideoLivreOr", "PanneauFontaine"), (), 800),
    ("duo-vip", "Pack Duo VIP", ("miroirbooth", "videobooth"),
     ("Phonebooth", "MurFloral"), (), 850),
    ("vogue-premium", "Pack Vogue Premium", ("voguebooth",),
     ("PhotographeVoguebooth", "ImpressionVoguebooth"), (), 700),
    ("mariage-prestige", "Pack Mariage Prestige", ("miroirbooth", "videobooth", "voguebooth"),
     ("Fond360", "MurFloral"), (), 1200),
)

PACK_BY_KEY = {p[0]: p for p in PACKS}
SOURCE_KEYS = {p[0] for p in SOURCES}
PRODUCT_KEYS = {p[0] for p in PRODUITS}
PACK_KEYS = {p[0] for p in PACKS}


def default_sources():
    return ["INSTAGRAM", "LINKEDIN", "SITE INTERNET", "LEBONCOIN"]


def default_products():
    # Ne pas activer automatiquement toutes les prestations avant validation.
    return ["photobooth"]


def default_pack_prices():
    return {pack[0]: pack[5] for pack in PACKS}


def default_product_prices():
    return dict(PRIX_VENTE_PAR_DEFAUT)
