from django.http import request


def update_data(event, request):

    client = event.client
    event_details = event.event_details
    event_product = event.event_product
    event_option = event.event_option

    # Mise à jour des informations du client
    client.nom = request.POST.get('client_nom')
    client.prenom = request.POST.get('client_prenom')
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

    # Mise à jour des options de l'événement
    event_option.mur_floral = request.POST.get('mur_floral') == 'on'
    event_option.phonebooth = request.POST.get('phonebooth') == 'on'
    event_option.magnets_value = request.POST.get('magnets', None)
    event_option.livraison = request.POST.get('livraison') == 'on'
    event_option.duree = request.POST.get('duree', None)
    event_option.save()

    # Mise à jour des autres informations de l'événement
    event.prix_brut = request.POST.get('prix_brut')

    def parse_int(value):
        return int(value) if value.strip() else None

    # Utilisez la fonction parse_int pour convertir les valeurs en entier ou en None si elles sont vides
    reduc_product = parse_int(request.POST.get('reduc_product', ''))
    reduc_all = parse_int(request.POST.get('reduc_all', ''))
    prix_proposed = parse_int(request.POST.get('prix_proposed', ''))

    # Mise à jour des valeurs de l'objet Event
    event.reduc_product = reduc_product
    event.reduc_all = reduc_all
    event.prix_proposed = prix_proposed

    event.save()

    return event