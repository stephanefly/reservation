"""Détail commercial des remises, basé sur la même grille brute que le PDF.

Aucune écriture ni modification de prix : le prix final est toujours
CatalogEntry.price, tandis que le prix de référence vient de PRIX_PRODUITS
et des méthodes prix_base_* de EventOption (tarification historique).
"""
from app.models import EventOption
from app.module.data_bdd.price import PRIX_PRODUITS
from .catalog import PRODUITS

PRODUCT_NAMES = dict(PRODUITS)


def get_offer_breakdown(item, entries_by_code):
    """Prix avant remise, composants et remise à partir d'une offre.

    Si une composition contient un code inconnu, ne pas fabriquer un
    ancien prix ni afficher une remise potentiellement trompeuse.
    """
    if item.kind not in ("product", "pack"):
        return {"available": False, "components": []}

    parts = []
    if item.kind == "product":
        base = PRIX_PRODUITS.get(item.code)
        if base is None:
            return {"available": False, "components": []}
        parts.append({"name": item.name, "quantity": 1, "unit": base, "total": base})
    else:
        options = EventOption()  # Objet mémoire sans sauvegarde.
        for code in item.product_codes or []:
            base = PRIX_PRODUITS.get(code)
            if base is None:
                return {"available": False, "components": []}
            named = entries_by_code.get(code)
            parts.append({
                "name": named.name if named else PRODUCT_NAMES.get(code, code),
                "quantity": 1, "unit": base, "total": base,
            })
        for code in item.option_codes or []:
            method = getattr(options, "prix_base_" + code, None)
            if not callable(method):
                return {"available": False, "components": []}
            try:
                base = int(method())
            except (TypeError, ValueError, AttributeError):
                return {"available": False, "components": []}
            named = entries_by_code.get(code)
            parts.append({
                "name": named.name if named else code,
                "quantity": 1, "unit": base, "total": base,
            })
        for code, raw_quantity in (item.quantities or {}).items():
            method = getattr(options, "prix_base_" + code, None)
            if not callable(method) or isinstance(raw_quantity, bool):
                return {"available": False, "components": []}
            try:
                quantity = int(raw_quantity)
                if quantity < 0 or quantity > 10000:
                    return {"available": False, "components": []}
                total = int(method(quantity))
            except (TypeError, ValueError, AttributeError):
                return {"available": False, "components": []}
            if quantity:
                named = entries_by_code.get(code)
                parts.append({
                    "name": named.name if named else code,
                    "quantity": quantity, "unit": total // quantity
                    if total % quantity == 0 else None, "total": total,
                })
        if not parts:
            return {"available": False, "components": []}

    reference = sum(part["total"] for part in parts)
    final = int(item.price)
    return {
        "available": True,
        "reference": reference,
        "discount": max(0, reference - final),
        "above_reference": final > reference,
        "final": final,
        "components": parts,
    }


def decorate_offers(entries):
    """Attacher les détails de prix aux objets pour les templates CRM."""
    entries = list(entries)
    lookup = {item.code: item for item in entries}
    for entry in entries:
        entry.pricing = get_offer_breakdown(entry, lookup)
    return entries
