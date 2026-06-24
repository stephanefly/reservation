from app.module.data_bdd.price import DEPARTEMENT_INCLUS, DEPARTEMENT_PLUS


def make_tableau(event):
    total_brut_devis = 0

    data_tableau_devis = [['Description', 'Prix unitaire', 'Quantité', 'Réduction', 'Total']]

    ligne_forfait, total_product, acompte = prix_ligne_product(event)
    data_tableau_devis.append(ligne_forfait)
    total_brut_devis += total_product

    livraison_details = "\n".join([
        str(event.event_details.date_evenement.strftime('%d/%m/%Y')),
        str(event.event_details.adresse_evenement),
        str(event.event_details.code_postal_evenement) + " " + str(event.event_details.ville_evenement)
    ])

    int_prix_livraison, str_prix_livraison = calcul_prix_distance(event)

    if event.event_option.livraison:
        data_tableau_devis.append([
            "Livraison - Installation\n" + livraison_details,
            str_prix_livraison,
            '1',
            "",
            str_prix_livraison
        ])
    else:
        data_tableau_devis.append([
            "Récupération avant le\n" + livraison_details,
            str_prix_livraison,
            '1',
            "",
            str_prix_livraison
        ])

    total_brut_devis += int_prix_livraison

    data_tableau_devis += [
        ['Personnalisation', '0 €', '1', "", '0 €'],
        ['Galerie Web', '0 €', '1', "", '0 €'],
    ]

    data_tableau_devis, total_option = prix_ligne_option(event, data_tableau_devis)
    total_brut_devis += total_option

    return data_tableau_devis, total_brut_devis, acompte


def prix_ligne_product(event):
    produits_descriptions = []

    if event.event_product.photobooth:
        if event.event_option.duree == 0:
            produits_descriptions.append("Photobooth 400 Tirages")
        else:
            produits_descriptions.append("Photobooth Tirages Illimités")

    if event.event_product.miroirbooth:
        produits_descriptions.append("Miroirbooth Tirages Illimités")

    if event.event_product.videobooth:
        produits_descriptions.append("360VidéoBooth Vidéos Illimités")

    if event.event_product.voguebooth:
        produits_descriptions.append("VogueBooth")

    if event.event_product.ipadbooth:
        produits_descriptions.append("Ipad Numérique Illimités")

    if event.event_product.airbooth:
        produits_descriptions.append("360Airbooth Vidéos Illimités")

    if len(produits_descriptions) > 1:
        acompte = "100"
    else:
        acompte = "50"

    if event.event_option.duree == 0:
        duree = "- Toute la soirée / Weekend"
    else:
        duree = "- " + str(event.event_option.duree) + "h"

    if event.reduc_product:
        total = event.prix_brut - event.reduc_product

        ligne_forfait = [
            "\n".join(produits_descriptions) + "\nDurée " + str(duree),
            str(event.prix_brut) + " €",
            '1',
            str(event.reduc_product) + " €",
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
    total = 0

    options_fixes = [
        (
            "Mur Floral / Backdrop",
            event.event_option.MurFloral,
            event.event_option.prix_base_MurFloral(),
            event.event_option.MurFloral_reduc_prix,
        ),
        (
            "PhoneBooth",
            event.event_option.Phonebooth,
            event.event_option.prix_base_Phonebooth(),
            event.event_option.Phonebooth_reduc_prix,
        ),
        (
            "Livre d'or personnalisé avec table et stylos",
            event.event_option.LivreOr,
            event.event_option.prix_base_LivreOr(),
            event.event_option.LivreOr_reduc_prix,
        ),
        (
            "Backdrop LightRGB 360",
            event.event_option.Fond360,
            event.event_option.prix_base_Fond360(),
            event.event_option.Fond360_reduc_prix,
        ),
        (
            "Panneau de Bienvenue personnalisé",
            event.event_option.PanneauBienvenue,
            event.event_option.prix_base_PanneauBienvenue(),
            event.event_option.PanneauBienvenue_reduc_prix,
        ),
        (
            "Panneau Hologramme 3D",
            event.event_option.Holo3D,
            event.event_option.prix_base_Holo3D(),
            event.event_option.Holo3D_reduc_prix,
        ),
        (
            "Panneau de Bienvenue Fontaine",
            event.event_option.PanneauFontaine,
            event.event_option.prix_base_PanneauFontaine(),
            event.event_option.PanneauFontaine_reduc_prix,
        ),
        (
            "Livre d'or Vidéo",
            event.event_option.VideoLivreOr,
            event.event_option.prix_base_VideoLivreOr(),
            event.event_option.VideoLivreOr_reduc_prix,
        ),
        (
            "Photographe pour le VogueBooth",
            event.event_option.PhotographeVoguebooth,
            event.event_option.prix_base_PhotographeVoguebooth(),
            event.event_option.PhotographeVoguebooth_reduc_prix,
        ),
        (
            "Impression pour le VogueBooth",
            event.event_option.ImpressionVoguebooth,
            event.event_option.prix_base_ImpressionVoguebooth(),
            event.event_option.ImpressionVoguebooth_reduc_prix,
        ),
        (
            "Décor personnalisé pour le VogueBooth",
            event.event_option.DecorVoguebooth,
            event.event_option.prix_base_DecorVoguebooth(),
            event.event_option.DecorVoguebooth_reduc_prix,
        ),
    ]

    for nom, condition, prix_base, reduc_prix in options_fixes:
        if condition:
            total += ajouter_ligne_option(
                data_tableau_devis=data_tableau_devis,
                description=nom,
                prix_total=prix_base,
                quantite=1,
                reduction=reduc_prix
            )

    if event.event_option.magnets:
        total += ajouter_ligne_option(
            data_tableau_devis=data_tableau_devis,
            description="Magnets photos",
            prix_total=event.event_option.prix_base_magnets(event.event_option.magnets),
            quantite=event.event_option.magnets,
            reduction=event.event_option.magnets_reduc_prix
        )

    if event.event_option.PorteCles:
        total += ajouter_ligne_option(
            data_tableau_devis=data_tableau_devis,
            description="Porte-clés",
            prix_total=event.event_option.prix_base_PorteCles(event.event_option.PorteCles),
            quantite=event.event_option.PorteCles,
            reduction=event.event_option.PorteCles_reduc_prix
        )

    if event.event_option.MagnetsSimple:
        total += ajouter_ligne_option(
            data_tableau_devis=data_tableau_devis,
            description="Magnets simples",
            prix_total=event.event_option.prix_base_MagnetsSimple(event.event_option.MagnetsSimple),
            quantite=event.event_option.MagnetsSimple,
            reduction=event.event_option.MagnetsSimple_reduc_prix
        )

    return data_tableau_devis, total


def ajouter_ligne_option(data_tableau_devis, description, prix_total, quantite, reduction=0):
    if not quantite:
        return 0

    if not reduction:
        reduction = 0

    prix_total_apres_reduction = prix_total - reduction

    if quantite > 0:
        prix_unitaire = prix_total / quantite
    else:
        prix_unitaire = prix_total

    data_tableau_devis.append([
        description,
        format_prix(prix_unitaire),
        str(quantite),
        format_prix(reduction) if reduction else "",
        format_prix(prix_total_apres_reduction),
    ])

    return prix_total_apres_reduction


def format_prix(prix):
    if prix == int(prix):
        return str(int(prix)) + " €"

    return str(round(prix, 2)) + " €"


def add_acompte_mention(event, data_tableau_devis, total_brut_devis):
    if event.event_acompte and int(event.event_acompte.montant_acompte) > 0:
        data_tableau_devis += [
            [
                'Acompte versé le ' + str(event.event_acompte.date_payement),
                str(event.event_acompte.montant_acompte) + ' €',
                '',
                "",
                "-" + str(event.event_acompte.montant_acompte) + ' €'
            ]
        ]

        total_brut_devis -= event.event_acompte.montant_acompte

    return data_tableau_devis, total_brut_devis


def calcul_prix_distance(event):
    departement = str(event.event_details.code_postal_evenement)[:2]

    if departement in DEPARTEMENT_INCLUS:
        return 0, "0 €"

    elif departement in DEPARTEMENT_PLUS:
        return 50, "50 €"

    else:
        return 100, "100 €"