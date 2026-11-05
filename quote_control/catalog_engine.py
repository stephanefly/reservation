"""Tarification des offres du catalogue, activee seulement sur demande expresse.

Ne touche ni aux champs event, ni au PDF, ni aux tarifs historiques des options.
Les conflits ou prix non representables par le PDF repassent en manuel.
"""
from app.module.data_bdd.event_pricing import OPTION_NAMES
from app.module.data_bdd.price import PRIX_PRODUITS

from .catalog_forms import QUANTITY_OPTIONS
from .models import CatalogEntry


def manual(reason):
    return {"eligible": False, "reason": reason}


def matched_pack(event, selection, pack):
    if set(pack.product_codes) != selection:
        return False
    if not all(bool(getattr(event.event_option, code, False)) for code in pack.option_codes):
        return False
    for code, quantity in pack.quantities.items():
        if code not in QUANTITY_OPTIONS:
            return False
        if (getattr(event.event_option, code, 0) or 0) < quantity:
            return False
    return True


def sum_included_options(event, pack):
    total = 0
    for code in pack.option_codes:
        total += getattr(event.event_option, "prix_base_" + code)()
    for code, count in pack.quantities.items():
        total += getattr(event.event_option, "prix_base_" + code)(count)
    return total


def analyse_catalog_quote(event, selection, duration, product_list, total_options, delivery):
    entries = list(CatalogEntry.objects.all())
    products = {x.code: x for x in entries if x.kind == "product"}
    options = {x.code: x for x in entries if x.kind == "option"}

    for code in selection:
        item = products.get(code)
        if not item or not item.active:
            return manual("Machine inactive ou absente du catalogue")

    # Une option dont le prix differe du calcul historique ne doit pas produire
    # un PDF portant un total different du devis calcule.
    for code in OPTION_NAMES:
        if not getattr(event.event_option, code, False):
            continue
        item = options.get(code)
        if item and (not item.active or item.price != getattr(event.event_option, "prix_base_" + code)()):
            return manual("Prix ou statut d'option non synchronise avec le PDF : devis manuel")
    for code in QUANTITY_OPTIONS:
        quantity = getattr(event.event_option, code, 0) or 0
        if not quantity:
            continue
        item = options.get(code)
        if item and (not item.active or item.price * quantity !=
                     getattr(event.event_option, "prix_base_" + code)(quantity)):
            return manual("Prix ou statut d'option quantite non synchronise avec le PDF : devis manuel")

    matches = []
    if duration == 5:
        matches = [x for x in entries if x.kind == "pack" and matched_pack(event, selection, x)]
    if len(matches) > 1:
        return manual("Plusieurs packs possibles : validation manuelle")
    if matches:
        pack = matches[0]
        if not pack.active or not pack.auto_enabled:
            return manual("Pack non active pour les devis automatiques")
        if any(not options.get(code) or not options[code].active for code in pack.option_codes):
            return manual("Option du pack absente ou inactive")
        if any(not options.get(code) or not options[code].active for code in pack.quantities):
            return manual("Option a quantite du pack absente ou inactive")
        if not all(products[code].active for code in pack.product_codes):
            return manual("Machine du pack inactive")
        try:
            discount = product_list + sum_included_options(event, pack) - pack.price
        except (AttributeError, ValueError, TypeError):
            return manual("Composition du pack invalide")
        if discount < 0:
            return manual("Prix du pack superieur aux elements separes")
        amount = product_list + total_options + delivery - discount
        label = pack.name
        pack_code = pack.code
        discount_product = 0
        discount_pack = discount
    elif len(selection) == 1:
        code = next(iter(selection))
        product = products[code]
        if not product.auto_enabled:
            return manual("Machine non activee pour les devis automatiques")
        if duration == 3:
            if code + "3h" not in PRIX_PRODUITS:
                return manual("Tarif 3 h non valide pour cette machine")
            discount_product = 0
        else:
            discount_product = product_list - product.price
            if discount_product < 0:
                return manual("Tarif machine superieur au prix brut du PDF")
        amount = product_list + total_options + delivery - discount_product
        discount_pack = 0
        pack_code = None
        label = product.name
    else:
        return manual("Combinaison sans pack du catalogue")

    if not 350 <= amount <= 100000:
        return manual("Tarif hors limites : validation manuelle")

    return {
        "eligible": True, "reason": "", "label": label, "pack": pack_code,
        "amount": amount,
        "calculation": {
            "prix_brut": product_list,
            "reduc_product": discount_product,
            "reduc_all": discount_pack,
            "prix_proposed": amount,
        },
    }
