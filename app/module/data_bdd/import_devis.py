import csv
import json
import datetime
from app.module.trello.get_trello_data import get_data_card


# from app.models import Client, EventDetails, EventOption, Event, EventProduct
# from django.db import transaction


def launch_import_data(json_filename, data_trello):
    with open(json_filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

        data_to_import = {}

        for client in data["quotations"]:
            data_client_to_import = {}

            #  -----------------------------------------------------------
            # DEVIS JSON ---------------------------------------------------
            try:
                data_client_to_import['nom'] = client['recipient']['name'].strip()
                data_client_to_import['raison_sociale'] = False
            except:
                data_client_to_import['nom'] = client['recipient']['company'].strip()
                data_client_to_import['raison_sociale'] = True

            # Vérification de la présence de l'email du destinataire et attribution en conséquence
            if client.get('recipient', {}).get('email', '') != '':
                data_client_to_import['mail'] = client['recipient']['email']
            else:
                data_client_to_import['mail'] = "contact@myselfiebooth-paris.fr"

            phones = client.get('recipient', {}).get('phones', [])
            if phones and phones[0] != '':
                data_client_to_import['numero_telephone'] = phones[0].replace(" ", "").replace(".", "")
            else:
                data_client_to_import['numero_telephone'] = "0699733998"

            data_client_to_import['prix_brut'] = client['pricePretax']
            data_client_to_import['reduc_all'] = client['reductionAmount']
            data_client_to_import['prix_proposed'] = client['price']
            if not client['uid'] == "Provisoire":
                data_client_to_import['prix_valided'] = client['price']
                data_client_to_import['status'] = 'Acompte OK'
            else:
                data_client_to_import['prix_valided'] = None
                data_client_to_import['status'] = 'Sended'

            date_create = datetime.datetime.utcfromtimestamp(client['createdAt'])
            data_client_to_import['created_at'] = date_create.strftime("%Y-%m-%d")

            try:
                date_signed = datetime.datetime.utcfromtimestamp(client['signer_at'])
                data_client_to_import['signer_at'] = date_signed.strftime("%Y-%m-%d")
            except:
                data_client_to_import['signer_at'] = None

            #  -----------------------------------------------------------
            # TRELLO -----------------------------------------------------------
            for card_trello in data_trello:
                if card_trello['name'] == data_client_to_import['nom']:

                    data_client_to_import['livraison'] = True

                    for label in card_trello['labels']:
                        if label['color'] == 'sky':
                            data_client_to_import['how_find'] = label['name']

                        if label['color'] == 'blue_dark':
                            data_client_to_import['photobooth'] = False
                            if label['name']=='Photobooth':
                                data_client_to_import['photobooth'] = True

                            data_client_to_import['miroirbooth'] = False
                            if label['name']=='Miroirbooth':
                                data_client_to_import['miroirbooth'] = True

                            data_client_to_import['videobooth'] = False
                            if label['name']=='360Booth':
                                data_client_to_import['videobooth'] = True

                        if label['color'] == 'blue':

                            data_client_to_import['mur_floral'] = False
                            if label['name'] == 'Mur Floral':
                                data_client_to_import['mur_floral'] = True

                            data_client_to_import['phonebooth'] = False
                            if label['name'] == 'Phonebooth':
                                data_client_to_import['phonebooth'] = True

                            data_client_to_import['livreor'] = False
                            if label['name'] == 'Livre d\'or':
                                data_client_to_import['livreor'] = True

                            data_client_to_import['magnets'] = False
                            if label['name'] == 'Livre d\'or':
                                data_client_to_import['livreor'] = True

                        if label['color'] == 'yellow_dark':
                                data_client_to_import['duree'] = label['name']

                    date_due = datetime.datetime.fromisoformat(card_trello['due'].replace('Z', '+00:00'))
                    data_client_to_import['date_evenement'] = date_due.strftime("%Y-%m-%d")




        # with transaction.atomic():
        #     client = Client(
        #         nom=data['recipient']['name'],
        #         mail=data['recipient']['email'],
        #         numero_telephone=data['recipient']['phones'],
        #         how_find=data['how_find'],
        #         raison_sociale=""
        #     )
        #     client.save()
        #
        #     event_details = EventDetails(
        #         date_evenement=data['date_evenement'],
        #         adresse_evenement=data['adresse_evenement'],
        #         ville_evenement=data['ville_evenement'],
        #         code_postal_evenement=data['code_postal_evenement'],
        #     )
        #     event_details.save()
        #
        #     event_product = EventProduct(
        #         photobooth=data['photobooth'],
        #         miroirbooth=data['miroirbooth'],
        #         videobooth=data['videobooth'],
        #     )
        #     event_product.save()
        #
        #     event_option = EventOption(
        #         mur_floral=data['mur_floral'],
        #         phonebooth=data['phonebooth'],
        #         livreor=data['livreor'],
        #         magnets=data['magnets'],
        #         duree=data['duree'],
        #     )
        #     event_option.save()
        #
        #     event = Event(
        #         client=client,
        #         event_details=event_details,
        #         event_product=event_product,
        #         event_option=event_option,
        #         duree=data['duree'],
        #         prix_brut=data['pricePretax'],
        #         reduc_all=data['reductionAmount'],
        #         prix_proposed=data['prix_proposed'],
        #         prix_valided=data['prix_valided'],
        #         created_at=data['created_at'],
        #         signer_at=data['signer_at'],
        #         status=data['status'],
        #     )
        #     event.save()

            data_to_import[data_client_to_import['nom']] = data_client_to_import
        print(str(len(data["quotations"])) + " / " + str(len(data_to_import)))
        print(data_to_import)

with open(r'C:\Users\s575264\PycharmProjects\reservation\app\module\data_bdd\card.json', 'r', encoding='utf-8') as file:
    data_trello = json.load(file)
launch_import_data(r"C:\Users\s575264\PycharmProjects\reservation\app\module\data_bdd\devis.json", data_trello)
