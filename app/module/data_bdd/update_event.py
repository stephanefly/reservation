from django.http import request


def parse_int(value, default=0):
    try:
        return int(value) if value is not None and value.strip() != '' else default
    except (ValueError, TypeError):
        return default


def update_event_option(request, event_option):
    # Définition des options avec leurs méthodes de prix de base et clés POST
    options = [
        {"name": "MurFloral", "prix_base_method": event_option.prix_base_MurFloral, "prix_brut": "MurFloral_reduc_prix"},
        {"name": "Phonebooth", "prix_base_method": event_option.prix_base_Phonebooth, "prix_brut": "Phonebooth_reduc_prix"},
        {"name": "LivreOr", "prix_base_method": event_option.prix_base_LivreOr, "prix_brut": "LivreOr_reduc_prix"},
        {"name": "Fond360", "prix_base_method": event_option.prix_base_Fond360,"prix_brut": "Fond360_reduc_prix"},
        {"name": "PanneauBienvenue", "prix_base_method": event_option.prix_base_PanneauBienvenue,"prix_brut": "PanneauBienvenue_reduc_prix"},
        {"name": "Holo3D", "prix_base_method": event_option.prix_base_Holo3D, "prix_brut": "Holo3D_reduc_prix"},
        # Magnets retiré de cette liste
        # Ajoutez d'autres options ici si nécessaire
    ]

    total_option = 0
    for option in options:
        option_active = request.POST.get(option["name"]) == 'on'
        reduc_prix = parse_int(request.POST.get(option["prix_brut"], 0))

        if option_active:
            setattr(event_option, option["name"], option_active)
            setattr(event_option, f"{option['name']}_reduc_prix", reduc_prix)

            prix_base = option["prix_base_method"]()
            total_option += prix_base - reduc_prix

    # Traitement spécifique pour les magnets après la boucle des autres options
    event_option.magnets = parse_int(request.POST.get('magnets', 0))
    event_option.magnets_reduc_prix = parse_int(request.POST.get('magnets_reduc_prix'))
    if event_option.magnets:
        # Assurez-vous que la méthode prix_base_magnets est bien définie pour accepter un paramètre dans votre modèle.
        total_option += event_option.prix_base_magnets(event_option.magnets) - event_option.magnets_reduc_prix

    event_option.save()
    return total_option


def update_data(event, request):

    client = event.client
    event_details = event.event_details
    event_product = event.event_product
    event_option = event.event_option

    # Mise à jour des informations du client
    client.nom = request.POST.get('client_nom')
    client.mail = request.POST.get('client_mail')
    client.numero_telephone = request.POST.get('client_numero_telephone')
    client.how_find = request.POST.get('client_how_find')
    client.save()

    # Mise à jour des détails de l'événement
    event_details.date_evenement = request.POST.get('date_evenement')
    event_details.adresse_evenement = request.POST.get('adresse_evenement')
    event_details.ville_evenement = request.POST.get('ville_evenement')
    event_details.code_postal_evenement = request.POST.get('code_postal_evenement')
    event_details.save()

    # Mise à jour des produits de l'événement
    event_product.photobooth = request.POST.get('photobooth') == 'on'
    event_product.miroirbooth = request.POST.get('miroirbooth') == 'on'
    event_product.videobooth = request.POST.get('videobooth') == 'on'
    event_product.save()

    # Mise à jour des options de l'événement et calcul du total
    total_option = update_event_option(request, event_option)

    # LIVRAISON
    event_option.MurFloral = request.POST.get('MurFloral') == 'on'
    event_option.Phonebooth = request.POST.get('Phonebooth') == 'on'
    event_option.LivreOr = request.POST.get('LivreOr') == 'on'
    event_option.Fond360 = request.POST.get('Fond360') == 'on'
    event_option.PanneauBienvenue = request.POST.get('PanneauBienvenue') == 'on'
    event_option.Holo3D = request.POST.get('Holo3D') == 'on'
    event_option.magnets = request.POST.get('magnets', '0')
    event_option.livraison = request.POST.get('livraison') == 'on'
    event_option.duree = request.POST.get('duree', '0')
    event_option.save()

    event.prix_brut = parse_int(request.POST.get('prix_brut'))
    event.reduc_product = parse_int(request.POST.get('reduc_product', '0'))
    event.reduc_all = parse_int(request.POST.get('reduc_all', '0'))

    event.prix_proposed = parse_int(request.POST.get('prix_proposed'))
    event.prix_proposed = event.prix_brut - event.reduc_product - event.reduc_all + total_option

    event.status = 'Calculed'
    event.save()

    return event