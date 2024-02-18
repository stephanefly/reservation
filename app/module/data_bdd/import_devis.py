import csv
import json
from datetime import datetime, timezone
# from app.models import Client, EventDetails, EventOption, Event, EventProduct
# from django.db import transaction
import re
import fitz  # PyMuPDF
import json


def launch_import_data(data, data_trello, event_locations):

    data_to_import = {}

    for client in data["quotations"]:
        data_client_to_import = {}

        #  -----------------------------------------------------------
        # DEVIS JSON ---------------------------------------------------
        try:
            data_client_to_import['nom'] = client['recipient']['name'].strip().replace("  ", " ")
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

        date_create = datetime.utcfromtimestamp(client['createdAt'])
        data_client_to_import['created_at'] = date_create.strftime("%Y-%m-%d")

        if client['signedAt']:
            date_signed = datetime.utcfromtimestamp(client['signedAt'])
            data_client_to_import['signer_at'] = date_signed.strftime("%Y-%m-%d")
        else:
            data_client_to_import['signer_at'] = None

        #  -----------------------------------------------------------
        # TRELLO -----------------------------------------------------------
        for card_trello in data_trello:
            if card_trello['name'] == data_client_to_import['nom']:

                data_client_to_import['livraison'] = True
                data_client_to_import['photobooth'] = False
                data_client_to_import['miroirbooth'] = False
                data_client_to_import['videobooth'] = False
                data_client_to_import['mur_floral'] = False
                data_client_to_import['phonebooth'] = False
                data_client_to_import['livreor'] = False
                data_client_to_import['magnets'] = False

                for label in card_trello['labels']:
                    if label['color'] == 'sky':
                        data_client_to_import['how_find'] = label['name']
                    else:
                        data_client_to_import['how_find'] ="INSTAGRAM"

                    if label['color'] == 'blue_dark':

                        if label['name']=='Photobooth':
                            data_client_to_import['photobooth'] = True

                        if label['name']=='Miroirbooth':
                            data_client_to_import['miroirbooth'] = True

                        if label['name']=='360Booth':
                            data_client_to_import['videobooth'] = True
                    else:
                        data_client_to_import['photobooth'] = True

                    if label['color'] == 'blue':

                        if label['name'] == 'Mur Floral':
                            data_client_to_import['mur_floral'] = True

                        if label['name'] == 'Phonebooth':
                            data_client_to_import['phonebooth'] = True

                        if label['name'] == 'Livre d\'or':
                            data_client_to_import['livreor'] = True

                        if label['name'] == 'Livre d\'or':
                            data_client_to_import['livreor'] = True

                    if label['color'] == 'yellow_dark':
                        data_client_to_import['duree'] = label['name']
                    else:
                        data_client_to_import['duree'] = 5

                date_due = datetime.fromisoformat(card_trello['due'].replace('Z', '+00:00'))
                data_client_to_import['date_evenement'] = date_due.strftime("%Y-%m-%d")


                # Obtenez l'heure actuelle, en utilisant le fuseau horaire UTC
                now = datetime.now(timezone.utc)
                if date_due <= now:
                    # Si la date de l'événement est postérieure à l'heure actuelle
                    data_client_to_import['status'] = 'Presta FINI' if client['uid'] != "Provisoire" else 'Refused'
                else:
                    # Si la date de l'événement est antérieure ou égale à l'heure actuelle
                    data_client_to_import['status'] = 'Acompte OK' if client['uid'] != "Provisoire" else 'Sended'


        #  -----------------------------------------------------------
        # DEVIS -----------------------------------------------------------
        for key, value in event_locations.items():
            if key == data_client_to_import['nom']:
                try:
                    data_client_to_import['adresse_evenement'] = value["adresse"]
                except:pass
                try:
                    data_client_to_import['ville_evenement'] = value["ville"]
                except:pass
                try:
                    data_client_to_import['code_postal_evenement'] = value["code_postal"]
                except:pass

                try:
                    data_client_to_import['created_at'] = value["created_at"]
                except:pass


        data_to_import[data_client_to_import['nom']] = data_client_to_import
    print(str(len(data["quotations"])) + " / " + str(len(data_to_import)))
    return data_to_import


def recup_devis_data(pdf_path):

    event_locations = {}
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")
            lines = text.split('\n')
            recipient_name = ""
            info = {}

            # daate_strin = "07 février 2024"
            # # Conversion de la date en utilisant babel
            # date_obj = parse_date(daate_strin, locale='fr_FR')
            #
            # # Affichage de la date
            # print(date_obj)



            for line in lines:
                if line == 'Destinataire':
                    recipient_name = lines[lines.index(line) + 1].strip()

                if 'Mise en Place' in line:
                    event_location_index = lines.index(line) + 5
                    event_location = lines[event_location_index].strip()
                    if event_location != 'Total':
                        info = {"adresse":event_location}

                if re.search(r'\b\d{5}\b', line):
                    postal_code = re.search(r'\b\d{5}\b', line).group()
                    if postal_code != '77176':
                        info["code_postal"]=postal_code

                        # Trouver l'index du code postal dans l'adresse
                        postal_code_index = line.find(postal_code)
                        words_after_postal_code = line[postal_code_index + len(postal_code):].strip().split()
                        event_locations[postal_code] = words_after_postal_code
                        info["ville"] = " ".join(words_after_postal_code)

            try:
                # Dictionnaire de mapping des mois français aux mois anglais
                mois_mapping = {
                    "janvier": "January",
                    "février": "February",
                    "mars": "March",
                    "avril": "April",
                    "mai": "May",
                    "juin": "June",
                    "juillet": "July",
                    "août": "August",
                    "septembre": "September",
                    "octobre": "October",
                    "novembre": "November",
                    "décembre": "December"
                }
                # Remplacer le nom du mois français par son équivalent anglais
                date_string = lines[1]
                for mois_fr, mois_en in mois_mapping.items():
                    if mois_fr in lines[1]:
                        date_string = date_string.replace(mois_fr, mois_en)
                        break
                date_format = "%d %B %Y"
                date_obj = datetime.strptime(date_string, date_format)
                date_str = date_obj.strftime("%Y-%m-%d")
                info["created_at"] = date_str

            except:pass
            event_locations[recipient_name] = info

    return event_locations


def correction(event):

    # Liste des clés de données attendues pour chaque client
    expected_keys = [
        "nom", "raison_sociale", "mail", "numero_telephone", "prix_brut", "reduc_all",
        "prix_proposed", "prix_valided", "status", "created_at", "signer_at", "livraison",
        "photobooth", "miroirbooth", "videobooth", "mur_floral", "phonebooth", "livreor",
        "magnets", "duree", "how_find", "date_evenement"
    ]

    i = 0
    for nom, data in event.items():
        missing_keys = [key for key in expected_keys if key not in data]

        if missing_keys:
            print(f"Nom: {nom}")
            print("Données manquantes:")
            i+=1
            for key in missing_keys:
                print(f"  {key}")
            print()  # Pour ajouter une ligne vide après l'affichage des données manquantes
    print(i)
    return event


def upload_all_data():

    pdf_path = r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\data_bdd\devis.pdf"
    event_locations = recup_devis_data(pdf_path)

    with open(r'C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\data_bdd\card.json', 'r',
              encoding='utf-8') as file:
        data_trello = json.load(file)
    with open(r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\data_bdd\devis.json", 'r',
              encoding='utf-8') as file:
        json_devis = json.load(file)

    event = launch_import_data(json_devis, data_trello, event_locations)

    event = correction(event)
    print(event)

    # for nom, data in event.items():
    #     print(data)

#         with transaction.atomic():
#             client = Client(
#                 nom=data['nom'],
#                 mail=data['mail'],
#                 numero_telephone=data['numero_telephone'],
#                 how_find=data['how_find'],
#                 raison_sociale=""
#             )
#             client.save()
#
#             event_details = EventDetails(
#                 date_evenement=data['date_evenement'])
#             try:
#                 event_details.adresse_evenement=data['adresse_evenement']
#             except:
#                 event_details.adresse_evenement = ""
#
#             try:
#                 event_details.ville_evenement=data['ville_evenement']
#             except:
#                 event_details.ville_evenement = ""
#
#             try:
#                 event_details.code_postal_evenement=data['code_postal_evenement']
#             except:
#                 event_details.code_postal_evenement = ""
#
#             event_details.save()
#
#             event_product = EventProduct()
#             try:
#                 event_option.photobooth = data['photobooth']
#             except:
#                 event_option.photobooth = False
#             try:
#                 event_option.miroirbooth = data['miroirbooth']
#             except:
#                 event_option.miroirbooth = False
#             try:
#                 event_option.videobooth = data['videobooth']
#             except:
#                 event_option.videobooth = False
#
#
#             event_option = EventOption()
#             try:
#                 event_option.mur_floral = data['mur_floral']
#             except:
#                 event_option.mur_floral = False
#             try:
#                 event_option.phonebooth = data['phonebooth']
#             except:
#                 event_option.phonebooth = False
#             try:
#                 event_option.livreor = data['livreor']
#             except:
#                 event_option.livreor = False
#             try:
#                 event_option.magnets = data['magnets']
#             except:
#                 event_option.magnets = False
#             try:
#                 event_option.duree = data['duree']
#             except:
#                 event_option.duree = "5h"
#             event_option.save()
#
#             event = Event(
#                 client=client,
#                 event_details=event_details,
#                 event_product=event_product,
#                 event_option=event_option,
#                 prix_brut=data['prix_brut'],
#                 reduc_all=data['reduc_all'],
#                 prix_proposed=data['prix_proposed'],
#                 prix_valided=data['prix_valided'],
#                 created_at=data['created_at'],
#                 signer_at=data['signer_at'],
#                 status=data['status'],
#             )
#             event.save()
#
upload_all_data()