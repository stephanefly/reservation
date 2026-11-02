TARIFS_PANNEAUX = {1: 150, 2: 300, 3: 350, 4: 400, 5: 450, 6: 500}
QUANTITE_PAR_DEFAUT = 4


def quantite_panneaux(post):
    if post.get("avec_panneaux") != "on":
        return 0
    valeur = post.get("panneaux_xxl", str(QUANTITE_PAR_DEFAUT))
    if valeur not in {str(q) for q in TARIFS_PANNEAUX}:
        raise ValueError("Choisissez entre 1 et 6 panneaux XXL.")
    return int(valeur)


def appliquer_panneaux(option, quantite, remise=0):
    # Conserver le forfait enregistré tant que la quantité reste la même.
    prix = TARIFS_PANNEAUX[quantite] if quantite else 0
    if quantite and option.panneaux_xxl == quantite and option.panneaux_forfait is not None:
        prix = option.panneaux_forfait
    try:
        remise = int(remise or 0) if quantite else 0
    except (ValueError, TypeError):
        raise ValueError("La remise des panneaux doit être un montant entier en euros.")
    if not 0 <= remise <= prix:
        raise ValueError("La remise ne peut pas dépasser le prix du lot de panneaux.")
    option.panneaux_xxl = quantite
    option.panneaux_forfait = prix
    option.panneaux_remise = remise
