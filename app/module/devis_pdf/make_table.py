
def make_tableau_devis(event):

    # Initialisation du tableau de devis avec l'en-tête
    data_tableau_devis = [['Description', 'Prix unitaire', 'Quantité', 'Réduction', 'Total']]

    ligne_forfait, acompte, total = prix_ligne_product(event)
    data_tableau_devis.append(ligne_forfait)

    # Ajout de la ligne de livraison avec les détails de l'événement
    livraison_details = "\n".join([
        str(event.event_details.date_evenement.strftime('%d/%m/%Y')),
        str(event.event_details.adresse_evenement),
        str(event.event_details.code_postal_evenement) + " " + str(event.event_details.ville_evenement)
    ])
    data_tableau_devis.append(["Livraison - Installation\n" + livraison_details, '0 €', '1', "", '0 €'])

    # Ajout des lignes fixes pour la personnalisation et la galerie web
    data_tableau_devis += [
        ['Personnalisation', '0 €', '1', "", '0 €'],
        ['Galerie Web', '0 €', '1', "", '0 €']
    ]

    data_tableau_devis = prix_ligne_option(event, data_tableau_devis)

    return data_tableau_devis, acompte


def prix_ligne_product(event):
    # Liste pour garder une trace des descriptions de produits
    produits_descriptions = []

    # Ajout des descriptions de produit en fonction des produits sélectionnés
    if event.event_product.photobooth:
        produits_descriptions.append("Photobooth Tirages Illimités ")
    if event.event_product.miroirbooth:
        produits_descriptions.append("Miroibooth Tirages Illimités ")
    if event.event_product.videobooth:
        produits_descriptions.append("360VidéoBooth Vidéos Illimités ")

    if len(produits_descriptions) > 1:
        acompte = "100"
    else:
        acompte = "50"

    total = str(event.prix_brut - event.reduc_product)

    # Ajout de la ligne du produit avec les détails de l'événement
    ligne_forfait = [
        "\n".join(produits_descriptions) + "\nDurée " + str(event.event_option.duree) + "h",
        str(event.prix_brut)+ " €",
        '1',
        str(event.reduc_product)+ " €",
        total + " €",
    ]

    return ligne_forfait, total, acompte

def prix_ligne_option(event, data_tableau_devis):

    # Vérifie si l'option Mur Floral est sélectionnée
    if event.event_option.mur_floral:

        # Initialisez le prix de base pour le mur floral
        prix_base = event.event_option.prix_base_mur_floral()

        # Vérifie si une réduction pour le mur floral est définie
        if event.event_option.mur_floral_reduc_prix:
            # Calculez le nouveau prix après réduction
            prix_apres_reduc = prix_base - event.event_option.mur_floral_reduc_prix
            ligne_mur_floral = ['Mur Floral / Backdrop',
                                f"{prix_base} €",
                                '1',
                                f"{event.event_option.mur_floral_reduc_prix} €",
                                f"{prix_apres_reduc} €"]
        else:
            # Aucune réduction n'est appliquée, le prix reste le même
            ligne_mur_floral = ['Mur Floral / Backdrop',
                                f"{prix_base} €",
                                '1',
                                "",
                                f"{prix_base} €"]

        # Ajoutez la ligne au tableau de devis
        data_tableau_devis.append(ligne_mur_floral)

    # Vérifie si l'option Mur Floral est sélectionnée
    if event.event_option.phonebooth:

        # Initialisez le prix de base pour le mur floral
        prix_base = event.event_option.prix_base_phonebooth()

        # Vérifie si une réduction pour le mur floral est définie
        if event.event_option.phonebooth_reduc_prix:
            # Calculez le nouveau prix après réduction
            prix_apres_reduc = prix_base - event.event_option.phonebooth_reduc_prix
            ligne_phonebooth = ['PhoneBooth',
                                f"{prix_base} €",
                                '1',
                                f"{event.event_option.phonebooth_reduc_prix} €",
                                f"{prix_apres_reduc} €"]
        else:
            # Aucune réduction n'est appliquée, le prix reste le même
            ligne_phonebooth = ['PhoneBooth',
                                f"{prix_base} €",
                                '1',
                                "",
                                f"{prix_base} €"]

        # Ajoutez la ligne au tableau de devis
        data_tableau_devis.append(ligne_phonebooth)

    # Vérifie si l'option Mur Floral est sélectionnée
    if event.event_option.magnets:

        # Initialisez le prix de base pour le mur floral
        prix_base = event.event_option.prix_base_magnets(event.event_option.magnets)

        # Vérifie si une réduction pour le mur floral est définie
        if event.event_option.magnets_reduc_prix:
            # Calculez le nouveau prix après réduction
            prix_apres_reduc = prix_base - event.event_option.magnets_reduc_prix
            ligne_magnet = [str(event.event_option.magnets)+' Magnets',
                                f"{prix_base} €",
                                '1',
                                f"{event.event_option.magnets_reduc_prix} €",
                                f"{prix_apres_reduc} €"]
        else:
            # Aucune réduction n'est appliquée, le prix reste le même
            ligne_magnet = [str(event.event_option.magnets)+' Magnets',
                                f"{prix_base} €",
                                '1',
                                "",
                                f"{prix_base} €"]

        # Ajoutez la ligne au tableau de devis
        data_tableau_devis.append(ligne_magnet)

    return data_tableau_devis