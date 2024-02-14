import csv
import json

from app.models import Client, EventDetails, EventOption, Event, EventProduct
from django.db import transaction


def launch_import_data(json_filename):
    with open(json_filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

        with transaction.atomic():
            client = Client(
                nom=data['recipient']['name'],
                mail=data['recipient']['email'],
                numero_telephone=data['recipient']['phones'],
                how_find=data['how_find'],
                raison_sociale=""
            )
            client.save()

            event_details = EventDetails(
                date_evenement=data['date_evenement'],
                adresse_evenement=data['adresse_evenement'],
                ville_evenement=data['ville_evenement'],
                code_postal_evenement=data['code_postal_evenement'],
            )
            event_details.save()

            event_product = EventProduct(
                photobooth=data['photobooth'],
                miroirbooth=data['miroirbooth'],
                videobooth=data['videobooth'],
            )
            event_product.save()

            event_option = EventOption(
                mur_floral=data['mur_floral'],
                phonebooth=data['phonebooth'],
                livreor=data['livreor'],
                magnets=data['magnets'],
                duree=data['duree'],
            )
            event_option.save()

            event = Event(
                client=client,
                event_details=event_details,
                event_product=event_product,
                event_option=event_option,
                duree=data['duree'],
                prix_brut=data['pricePretax'],
                reduc_all=data['reductionAmount'],
                prix_proposed=data['prix_proposed'],
                prix_valided=data['prix_valided'],
                created_at=data['created_at'],
                signer_at=data['signer_at'],
                status=data['status'],
            )
            event.save()