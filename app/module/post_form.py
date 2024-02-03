from app.models import Client, EventDetails, EventProduct, EventOption, Event
from django.db import transaction

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
            prenom=client_data['prenom'],
            mail=client_data['mail'],
            numero_telephone=client_data['telephone'],
            how_find=client_data['how_find']
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
            prix_brut=0,  # Définissez une valeur initiale ou récupérez-la de post_data si disponible
            # prix_proposed et prix_valided peuvent rester à None si non spécifiés initialement
            # status='Initied',  # Ou un autre statut initial selon la logique de votre application
        )
        event.save()
