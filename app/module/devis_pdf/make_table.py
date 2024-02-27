
def make_tableau_devis(event):
    total_brut_devis=0
    # Initialisation du tableau de devis avec l'en-tête
    data_tableau_devis = [['Description', 'Prix unitaire', 'Quantité', 'Réduction', 'Total']]

    ligne_forfait, total_product, acompte = prix_ligne_product(event)
    data_tableau_devis.append(ligne_forfait)
    total_brut_devis += total_product

    # Ajout de la ligne de livraison avec les détails de l'événement
    livraison_details = "\n".join([
        str(event.event_details.date_evenement.strftime('%d/%m/%Y')),
        str(event.event_details.adresse_evenement),
        str(event.event_details.code_postal_evenement) + " " + str(event.event_details.ville_evenement)
    ])
    if str(event.event_details.code_postal_evenement)[:2] in ['75','77', '27', '78', '95', '92', '94', '91', '93']:
        data_tableau_devis.append(["Livraison - Installation\n" + livraison_details, '0 €', '1', "", '0 €'])
    else:
        data_tableau_devis.append(["Livraison - Installation (Hors IDF)\n" + livraison_details, '0 €', '1', "", '50 €'])
        total_brut_devis += 50

    # Ajout des lignes fixes pour la personnalisation et la galerie web
    data_tableau_devis += [
        ['Personnalisation', '0 €', '1', "", '0 €'],
        ['Galerie Web', '0 €', '1', "", '0 €']
    ]

    data_tableau_devis, total_option = prix_ligne_option(event, data_tableau_devis)

    total_brut_devis += total_option

    return data_tableau_devis, total_brut_devis, acompte


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

    if event.event_option.duree == 0:
        duree = "- Toute la soirée"
    else:
        duree = " - " + str(event.event_option.duree) + "h"

    if event.reduc_product:
        total = event.prix_brut - event.reduc_product
        # Ajout de la ligne du produit avec les détails de l'événement
        ligne_forfait = [
            "\n".join(produits_descriptions) + "\nDurée " + str(duree),
            str(event.prix_brut)+ " €",
            '1',
            str(event.reduc_product)+ " €",
            str(total) + " €",
        ]

    else:
        total = event.prix_brut
        ligne_forfait = [
            "\n".join(produits_descriptions) + "\nDurée " + str(duree),
            str(total) + " €",
            '1',
            "",
            str(total) + " €",
        ]

    return ligne_forfait, total, acompte


def prix_ligne_option(event, data_tableau_devis):
    options = [
        ("Mur Floral / Backdrop", event.event_option.MurFloral, event.event_option.prix_base_MurFloral(), event.event_option.MurFloral_reduc_prix),
        ("PhoneBooth", event.event_option.Phonebooth, event.event_option.prix_base_Phonebooth(), event.event_option.Phonebooth_reduc_prix),
        ("Livre d'or personnalisé avec table et stylos", event.event_option.LivreOr, event.event_option.prix_base_LivreOr(),event.event_option.LivreOr_reduc_prix),
        ("Backdrop LightRGB 360", event.event_option.Fond360, event.event_option.prix_base_Fond360(),event.event_option.Fond360_reduc_prix),
        ("Panneau de Bienvenue personnalisé", event.event_option.PanneauBienvenue, event.event_option.prix_base_PanneauBienvenue(),event.event_option.PanneauBienvenue_reduc_prix),
        ("Panneau Holograme 3D", event.event_option.Holo3D,event.event_option.prix_base_Holo3D(), event.event_option.Holo3D_reduc_prix),
        ("100 Magnets", event.event_option.magnets, event.event_option.prix_base_magnets(event.event_option.magnets) if event.event_option.magnets else 0, event.event_option.magnets_reduc_prix)
    ]

    total=0

    for nom, condition, prix_base, reduc_prix in options:
        if condition:
            # Calculez le prix après réduction s'il y a une réduction, sinon utilisez le prix de base
            prix_apres_reduc = prix_base - reduc_prix if reduc_prix else prix_base
            # Créez la ligne avec le prix après réduction ou le prix de base si aucune réduction
            ligne = [
                f"{nom}",
                f"{prix_base} €",
                "1",
                f"{reduc_prix} €" if reduc_prix else "",
                f"{prix_apres_reduc} €"
            ]
            total += prix_apres_reduc
            # Ajoutez la ligne au tableau de devis
            data_tableau_devis.append(ligne)

    return data_tableau_devis, total
