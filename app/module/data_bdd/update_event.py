from django.http import request


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

    def parse_int(value, default=0):
        try:
            return int(value) if value is not None and value.strip() != '' else default
        except (ValueError, TypeError):
            return default

    # Mise à jour des options de l'événement
    event_option.mur_floral = request.POST.get('mur_floral') == 'on'
    event_option.mur_floral_reduc_prix = parse_int(request.POST.get('mur_floral_reduc_prix'))

    event_option.phonebooth = request.POST.get('phonebooth') == 'on'
    event_option.phonebooth_reduc_prix = parse_int(request.POST.get('phonebooth_reduc_prix'))

    event_option.magnets = parse_int(request.POST.get('magnets', 0))
    event_option.magnets_reduc_prix = parse_int(request.POST.get('magnets_reduc_prix'))

    event_option.livraison = request.POST.get('livraison') == 'on'
    event_option.duree = request.POST.get('duree', None)
    event_option.save()


    event.prix_brut = parse_int(request.POST.get('prix_brut'))
    event.reduc_product = parse_int(request.POST.get('reduc_product', '0'))
    event.reduc_all = parse_int(request.POST.get('reduc_all', '0'))
    event.prix_proposed = parse_int(request.POST.get('prix_proposed'))

    event.prix_proposed = event.prix_brut - event.reduc_product - event.reduc_all

    event.save()

    return event