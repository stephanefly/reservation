"""Préparation d'un devis automatique à partir des tarifs du CRM.

La source RECOMMANDATION et les entreprises restent en traitement manuel.
Aucun paiement ni signature ne sont déclenchés ici.
"""

from app.module.data_bdd.event_pricing import calculate_option_total
from app.module.data_bdd.price import PRIX_PRODUITS
from app.module.devis_pdf.make_table import calcul_prix_distance

SOURCES_AUTOMATIQUES = frozenset({
    "INSTAGRAM", "LINKEDIN", "SITE INTERNET", "LEBONCOIN",
})

PRODUITS = {
    "photobooth": "photobooth",
    "miroirbooth": "miroirbooth",
    "videobooth": "videobooth",
    "voguebooth": "voguebooth",
    "ipadbooth": "ipadbooth",
    "airbooth": "airbooth",
}


def devis_automatique_autorise(client):
    """Ne jamais envoyer un devis automatique à une recommandation ou à un pro."""
    source = (getattr(client, "how_find", "") or "").strip().upper()
    return source in SOURCES_AUTOMATIQUES and not bool(getattr(client, "raison_sociale", False))


def calculer_devis_instantane(event):
    """Renvoyer le calcul de prix validable, ou lever ValueError pour gestion manuelle."""
    duree = getattr(event.event_option, "duree", None)
    if duree not in (3, 4, 5, 6, 7):
        raise ValueError("Durée non couverte par le devis instantané.")

    # Les codes postaux avec zéro initial sont actuellement convertis en entier
    # par le CRM : ne pas estimer une livraison sur cette donnée incomplète.
    code_postal = str(event.event_details.code_postal_evenement)
    if len(code_postal) != 5 or not code_postal.isdigit():
        raise ValueError("Code postal à vérifier manuellement.")

    selection = [
        produit for attribut, produit in PRODUITS.items()
        if getattr(event.event_product, attribut, False)
    ]
    if not selection:
        raise ValueError("Aucune prestation sélectionnée.")

    # Base de prix du CRM : tarif 3 h si prévu, tarif standard sinon.
    prix_brut = 0
    for produit in selection:
        cle = produit + "3h" if duree == 3 and produit + "3h" in PRIX_PRODUITS else produit
        prix_brut += PRIX_PRODUITS[cle]

    # Conserver les réductions de produits existantes, sans en créer de nouvelles :
    # 50 € pour le Photobooth standard seul, 250 € pour le combo à 1 100 €.
    reduction = 0
    if duree != 3 and selection == ["photobooth"] and prix_brut == 450:
        reduction = 50
    elif duree != 3 and len(selection) > 1 and prix_brut == 1100:
        reduction = 250

    options = calculate_option_total(event.event_option)
    livraison, _ = calcul_prix_distance(event)
    total = prix_brut - reduction + options + livraison
    if total < 350:
        raise ValueError("Montant inférieur au seuil commercial : validation manuelle.")

    return {
        "prix_brut": prix_brut,
        "reduc_product": reduction,
        "prix_proposed": total,
    }


def preparer_et_envoyer_devis(event, envoyer_mail):
    """Préparer, puis envoyer le devis si le client est éligible.

    True signifie que le mail a été accepté par l'outil d'envoi.
    False signifie que la demande reste à traiter manuellement.
    """
    if not devis_automatique_autorise(event.client):
        return False

    montants = calculer_devis_instantane(event)
    for nom, valeur in montants.items():
        setattr(event, nom, valeur)

    event.status = "Calculed"
    event.save()

    if not envoyer_mail(event, "devis"):
        return False

    event.status = "Sended"
    event.save(update_fields=["status"])
    return True
