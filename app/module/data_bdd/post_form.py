from app.models import Client, EventDetails, EventProduct, EventOption, Event
from django.db import transaction
from datetime import datetime

def get_confirmation_data(request):
    if request.POST.get('raison_sociale'):
        nom = request.POST.get('raison_sociale').strip()
        raison_sociale = True
    else:
        nom = request.POST.get('prenom').strip() + " " + request.POST.get('nom').strip()
        raison_sociale = False

    print(int(request.POST.get('magnets_range')))

    post_data = {
        "page_client": {
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
        "options": request.POST.get('selectedOption'),
        "magnets_range": int(request.POST.get('magnets_range')),
        "livraison": True if request.POST.get('livraison') else False,
        "heure_range": int(request.POST.get('heure_range')) if request.POST.get('heure_range') else None
    }
    return post_data

def initialize_event(post_data):
    print("initialize_event : " +str(post_data))

    with transaction.atomic():
        # -------------------------------------------------------------
        client_data = post_data['page_client']
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
            'voguebooth': False,
            'ipadbooth': False,
            'airbooth': False,
        }

        # Mise à jour des attributs en fonction de la présence des mots-clés dans product_data
        if "Photobooth" in product_data:
            product_attrs['photobooth'] = True
        if "Miroirbooth" in product_data:
            product_attrs['miroirbooth'] = True
        if "360Booth" in product_data:
            product_attrs['videobooth'] = True
        if "Voguebooth" in product_data:
            product_attrs['voguebooth'] = True
        if "Ipadbooth" in product_data:
            product_attrs['ipadbooth'] = True
        if "360Airbooth" in product_data:
            product_attrs['airbooth'] = True

        # Création et sauvegarde de l'objet EventProduct avec les attributs mis à jour
        event_product = EventProduct(**product_attrs)
        event_product.save()
        # -------------------------------------------------------------
        # Création et sauvegarde de l'objet EventOption
        # Initialisation des attributs d'options avec les valeurs par défaut à False
        options_attrs = {
            'MurFloral': False,
            'Phonebooth': False,
            'LivreOr': False,
            'Fond360': False,
            'PanneauBienvenue': False,
            'Holo3D': False,
        }

        # Convertissez options_data en une liste si ce n'est pas déjà le cas
        # Assumons que options_data peut être une chaîne avec des options séparées par des virgules
        options_list = options_data.split(',') if isinstance(options_data, str) else options_data
        # Mise à jour des attributs en fonction de la présence des options dans options_data
        for option in options_attrs.keys():
            if option in options_list:
                options_attrs[option] = True

        # Création et sauvegarde de l'objet EventProduct avec les attributs mis à jour
        event_option = EventOption(**options_attrs)
        event_option.magnets = post_data['magnets_range']
        event_option.livraison = post_data['livraison']
        event_option.duree = post_data['heure_range']
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
        event.save()

        make_num_devis(event)
        event.prix_brut = prix_brut_calculs(event)
        event.save()

        return event

def prix_brut_calculs(event):
    prix_brut = 0

    # Prix de base pour chaque produit pour des durées de 5 et 3 heures
    prix_photobooth_5h = 450
    prix_miroirbooth_5h = 550
    prix_360booth_5h = 500
    prix_voguebooth_5h = 500
    prix_ipadbooth_5h = 250
    prix_airbooth_5h = 500

    # Ajoutez le prix de chaque produit sélectionné
    if event.event_product.photobooth:
        prix_brut += prix_photobooth_5h
    if event.event_product.miroirbooth:
        prix_brut += prix_miroirbooth_5h
    if event.event_product.videobooth:
        prix_brut += prix_360booth_5h
    if event.event_product.voguebooth:
        prix_brut += prix_voguebooth_5h
    if event.event_product.ipadbooth:
        prix_brut += prix_ipadbooth_5h
    if event.event_product.airbooth:
        prix_brut += prix_airbooth_5h

    if prix_brut == 450:
        event.reduc_product = 50
    if prix_brut == 1100:
        event.reduc_product = 250

    return prix_brut

def make_num_devis(event):

    # Obtenir la date actuelle
    today = datetime.now()
    # Formater la date en 'YYMMDD'
    formatted_date = today.strftime("%y%m")

    # Concaténer la date formatée avec l'ID de l'objet
    event.num_devis = formatted_date + str(event.id) + '0'
    event.save()
