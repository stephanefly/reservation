"""Décision et calcul de devis : aucune écriture DB ni envoi de mail ici."""

from app.module.data_bdd.event_pricing import calculate_option_total
from app.module.data_bdd.price import PRIX_PRODUITS
from app.module.devis_pdf.make_table import calcul_prix_distance
from .catalog import PACKS, PACK_BY_KEY, PRODUCT_KEYS, SOURCE_KEYS

MANUAL_SOURCES = {"RECOMMANDATION", "RECOMMENDATION"}


def selected_products(event):
    return {
        key for key in PRODUCT_KEYS
        if bool(getattr(event.event_product, key, False))
    }


def match_pack(event, selection):
    """Le pack ne peut être reconnu qu'avec toutes ses options incluses."""
    for pack in PACKS:
        key, name, products, options, quantities, price = pack
        if selection != set(products):
            continue
        if not all(bool(getattr(event.event_option, option, False)) for option in options):
            continue
        if not all((getattr(event.event_option, field, 0) or 0) >= required
                   for field, required in quantities):
            continue
        return key
    return None


def included_option_price(event, pack):
    total = 0
    for option in pack[3]:
        total += getattr(event.event_option, "prix_base_" + option)()
    for option, quantity in pack[4]:
        total += getattr(event.event_option, "prix_base_" + option)(quantity)
    return total


def analyse_quote(event, config, preview=False):
    """Retourne un résultat d'analyse exploitable par l'UI et par le moteur.

    Refuse systématiquement les entreprises, les recommandations,
    les packs non activés, les compositions inconnues et les prix douteux.
    """
    source = (getattr(event.client, "how_find", None) or "").strip().upper()
    if getattr(event.client, "raison_sociale", False):
        return {"eligible": False, "reason": "Entreprise : traitement manuel"}
    if source in MANUAL_SOURCES:
        return {"eligible": False, "reason": "Recommandation : traitement manuel"}
    if source not in SOURCE_KEYS or source not in config.sources:
        return {"eligible": False, "reason": "Source non autorisée"}
    if not config.enabled and not preview:
        return {"eligible": False, "reason": "Automatisation désactivée"}

    selection = selected_products(event)
    if not selection:
        return {"eligible": False, "reason": "Aucune prestation sélectionnée"}
    duration = getattr(event.event_option, "duree", None)
    if duration not in (3, 5):
        return {"eligible": False, "reason": "Durée hors des formules 3 h et 5 h"}

    postcode = str(getattr(event.event_details, "code_postal_evenement", ""))
    if len(postcode) != 5 or not postcode.isdigit():
        return {"eligible": False, "reason": "Code postal à vérifier manuellement"}

    try:
        product_list = sum(PRIX_PRODUITS[key + "3h" if duration == 3
            and key + "3h" in PRIX_PRODUITS else key] for key in selection)
        total_options = calculate_option_total(event.event_option)
        delivery, _ = calcul_prix_distance(event)
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"eligible": False, "reason": "Tarification à vérifier"}

    pack_key = match_pack(event, selection) if duration == 5 else None
    discount_product = 0
    discount_pack = 0
    label = "Prestation"

    if pack_key:
        if pack_key not in config.packs:
            return {"eligible": False, "reason": "Pack non activé pour l'envoi automatique"}
        pack = PACK_BY_KEY[pack_key]
        try:
            target_price = int(config.pack_prices.get(pack_key, pack[5]))
            discount_pack = product_list + included_option_price(event, pack) - target_price
        except (ValueError, TypeError, AttributeError):
            return {"eligible": False, "reason": "Prix du pack invalide"}
        if discount_pack < 0:
            return {"eligible": False, "reason": "Prix du pack supérieur au tarif séparé"}
        label = pack[1]
    elif len(selection) == 1:
        key = next(iter(selection))
        if key not in config.products:
            return {"eligible": False, "reason": "Prestation non activée"}
        if duration == 3 and key + "3h" not in PRIX_PRODUITS:
            return {"eligible": False, "reason": "Pas de tarif 3 h validé pour cette machine"}
        if duration == 5:
            try:
                target_price = int(config.product_prices.get(key, PRIX_PRODUITS[key]))
            except (ValueError, TypeError, AttributeError):
                return {"eligible": False, "reason": "Prix de la machine invalide"}
            discount_product = product_list - target_price
            if discount_product < 0:
                return {"eligible": False, "reason": "Prix supérieur à la base CRM"}
        label = key
    else:
        return {"eligible": False, "reason": "Combinaison sans pack reconnu"}

    amount = product_list - discount_product + total_options + delivery - discount_pack
    if not 350 <= amount <= 100000:
        return {"eligible": False, "reason": "Prix hors limites : vérification manuelle"}

    return {
        "eligible": True,
        "reason": "",
        "label": label,
        "pack": pack_key,
        "amount": amount,
        "calculation": {
            "prix_brut": product_list,
            "reduc_product": discount_product,
            "reduc_all": discount_pack,
            "prix_proposed": amount,
        },
    }
