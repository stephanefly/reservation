from app.models import Client, EventDetails, EventProduct, EventOption, Event
from django.db import transaction

def get_confirmation_data(request):
    if request.POST.get('raison_sociale'):
        nom = request.POST.get('raison_sociale').strip()
        raison_sociale = True
    else:
        nom = request.POST.get('nom').strip() + " " + request.POST.get('prenom').strip()
        raison_sociale = False

    post_data = {
        "client": {
            "nom": nom,
            "raison_sociale": raison_sociale,
            "mail": request.POST.get('mail').strip(),
            "telephone": request.POST.get('numero_telephone').strip(),
            "how_find": request.POST.get('client_how_find'),
        },
        "event": {
            "date": request.POST.get('date_evenement'),
            "adresse": request.POST.get('adresse_evenement'),
            "ville": request.POST.get('ville_evenement'),
            "code_postal": request.POST.get('code_postal_evenement').strip(),
        },
        "product": request.POST.get('selectedImages'),
        "options": {
            "murfloral": True if request.POST.get('murfloral') else False,
            "phonebooth": True if request.POST.get('phonebooth') else False,
            "livreor": True if request.POST.get('livreor') else False,
            "magnets_range": int(request.POST.get('magnets_range', 0)) if int(
                request.POST.get('magnets_range', 0)) > 0 else None,
            "livraison": True if request.POST.get('livraisonInstallation') else False,
            "heure_range": int(request.POST.get('heure_range', 0))
        }
    }
    return post_data

def initialize_event(post_data):
    print(post_data)

    with transaction.atomic():
        # -------------------------------------------------------------
        client_data = post_data['client']
        event_data = post_data['event']
        product_data = post_data['product']
        options_data = post_data['options']
        # -------------------------------------------------------------
        # Création et sauvegarde de l'objet Client
        client = Client(
            nom=client_data['nom'],
            mail=client_data['mail'],
            numero_telephone=client_data['telephone'].strip(),
            how_find=client_data['how_find'],
            raison_sociale=client_data['raison_sociale'],
        )
        client.save()
        # -------------------------------------------------------------
        # Création et sauvegarde de l'objet EventDetails
        event_details = EventDetails(
            date_evenement=event_data['date'],
            adresse_evenement=event_data['adresse'],
            ville_evenement=event_data['ville'],
            code_postal_evenement=event_data['code_postal']
        )
        event_details.save()
        # -------------------------------------------------------------
        # Initialisation des attributs du produit à False
        product_attrs = {
            'photobooth': False,
            'miroirbooth': False,
            'videobooth': False,
        }

        # Mise à jour des attributs en fonction de la présence des mots-clés dans product_data
        if "Photobooth" in product_data:
            product_attrs['photobooth'] = True
        if "Miroirbooth" in product_data:
            product_attrs['miroirbooth'] = True
        if "360Booth" in product_data:
            product_attrs['videobooth'] = True

        # Création et sauvegarde de l'objet EventProduct avec les attributs mis à jour
        event_product = EventProduct(**product_attrs)
        event_product.save()
        # -------------------------------------------------------------
        # Création et sauvegarde de l'objet EventOption
        # Assumons 'duree' doit être un booléen, donc vérifions si 'heure_range' est spécifié pour définir la valeur
        event_option = EventOption(
            mur_floral=options_data['murfloral'],
            phonebooth=options_data['phonebooth'],
            livreor=options_data['livreor'],
            magnets=options_data['magnets_range'],
            livraison=options_data['livraison'],
            duree=options_data['heure_range'], # Utilisez une logique appropriée pour déterminer la valeur booléenne
        )
        event_option.save()
        # -------------------------------------------------------------


        # Création de l'objet Event
        event = Event(
            client=client,
            event_details=event_details,
            event_product=event_product,
            event_option=event_option,
            prix_brut=0,
        )
        event.prix_brut = prix_brut_calculs(event)
        event.save()

def prix_brut_calculs(event):
    prix_brut = 0

    # Prix de base pour chaque produit pour des durées de 5 et 3 heures
    prix_photobooth_5h, prix_miroirbooth_5h, prix_360booth_5h = 450, 600, 500

    # Ajoutez le prix de chaque produit sélectionné
    if event.event_product.photobooth:
        prix_brut += prix_photobooth_5h
    if event.event_product.miroirbooth:
        prix_brut += prix_miroirbooth_5h
    if event.event_product.videobooth:
        prix_brut += prix_360booth_5h

    if prix_brut == 450:
        event.reduc_product = 50
    if prix_brut == 1100:
        event.reduc_product = 250

    return prix_brut