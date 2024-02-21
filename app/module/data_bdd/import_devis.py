import csv
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from datetime import datetime, timezone
from app.models import Client, EventDetails, EventOption, Event, EventProduct
from django.db import transaction
import re
import fitz  # PyMuPDF
import json
import random

def recup_devis_data(pdf_path):

    event_locations = {}
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")
            lines = text.split('\n')
            recipient_name = ""
            info = {}

            if not "Devis" in str(lines[0]):
                continue

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

            # Définir la période de temps durant laquelle les dates seront ajustées
            start_date = datetime(2024, 2, 14)
            end_date = datetime(2024, 2, 20)
            if start_date <= date_obj <= end_date:
                start_of_2023 = datetime(2023, 1, 1)
                end_of_2023 = datetime(2023, 12, 31)
                date_obj = start_of_2023 + timedelta(days=random.randint(0, (end_of_2023 - start_of_2023).days))


            date_str = date_obj.strftime("%Y-%m-%d")
            info["created_at"] = date_str
            event_locations[recipient_name] = info

    return event_locations

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

        if client['signedAt']:
            date_signed = datetime.utcfromtimestamp(client['signedAt'])
            data_client_to_import['signer_at'] = date_signed.strftime("%Y-%m-%d")
            data_client_to_import['prix_valided'] = client['price']
        else:
            data_client_to_import['signer_at'] = None
            data_client_to_import['prix_valided'] = None

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
                data_client_to_import['how_find'] = "INSTAGRAM"

                for label in card_trello['labels']:
                    if label['color'] == 'sky':
                        data_client_to_import['how_find'] = label['name']

                    elif label['color'] == 'blue_dark':

                        if label['name'] == 'Photobooth':
                            data_client_to_import['photobooth'] = True

                        if label['name'] == 'Miroirbooth':
                            data_client_to_import['miroirbooth'] = True

                        if label['name'] == '360Booth':
                            data_client_to_import['videobooth'] = True

                    elif label['color'] == 'blue':

                        if label['name'] == 'Mur Floral':
                            data_client_to_import['mur_floral'] = True

                        if label['name'] == 'Phonebooth':
                            data_client_to_import['phonebooth'] = True

                        if label['name'] == 'Livre d\'or':
                            data_client_to_import['livreor'] = True

                        if label['name'] == 'Livre d\'or':
                            data_client_to_import['livreor'] = True

                    elif label['color'] == 'yellow_dark':
                        if label['name'] == "LOCATION":
                            data_client_to_import['duree'] = 0
                        try :
                            data_client_to_import['duree'] = int(label['name'].replace("h",""))
                        except:
                            data_client_to_import['duree'] = 5

                date_due = datetime.fromisoformat(card_trello['due'].replace('Z', '+00:00'))
                data_client_to_import['date_evenement'] = date_due.strftime("%Y-%m-%d")

                # Obtenez l'heure actuelle, en utilisant le fuseau horaire UTC
                now = datetime.now(timezone.utc)
                if date_due <= now:
                    # Si la date de l'événement est postérieure à l'heure actuelle
                    data_client_to_import['status'] = 'Presta FINI' if client["signedAt"] else 'Refused'
                else:
                    # Si la date de l'événement est antérieure ou égale à l'heure actuelle
                    data_client_to_import['status'] = 'Acompte OK' if client["signedAt"] else 'Sended'


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

                if not value["created_at"]:
                    date_create = datetime.utcfromtimestamp(client["created_at"])
                    data_client_to_import['created_at'] = date_create.strftime("%Y-%m-%d")
                else:
                    data_client_to_import['created_at'] = value["created_at"]


        data_to_import[data_client_to_import['nom']] = data_client_to_import
    print(str(len(data["quotations"])) + " / " + str(len(data_to_import)))
    return data_to_import


def upload_all_data():

    with open(r'app/module/data_bdd/card.json', 'r',
              encoding='utf-8') as file:
        data_trello = json.load(file)
    with open(r"app/module/data_bdd/devis.json", 'r',
              encoding='utf-8') as file:
        json_devis = json.load(file)
    pdf_path = r"app/module/data_bdd/devis.pdf"

    event_locations = recup_devis_data(pdf_path)

    event_presta = launch_import_data(json_devis, data_trello, event_locations)

    i=0
    for nom, data in event_presta.items():

        if Client.objects.filter(nom=nom):
            for client in Client.objects.filter(nom=nom):
                event = Event.objects.get(client=client)
                event.event_details.delete()
                event.event_product.delete()
                event.event_option.delete()
                client.delete()
                event.delete()

        with transaction.atomic():
            client = Client(
                nom=data['nom'],
                raison_sociale=data['raison_sociale'],
                mail=data['mail'],
                how_find=data['how_find'],
                numero_telephone= data['numero_telephone'],
            )

            client.save()

            event_details = EventDetails(
                date_evenement=data['date_evenement'],)
            try:
                event_details.adresse_evenement=data['adresse_evenement']
            except:
                event_details.adresse_evenement = ""

            try:
                event_details.ville_evenement=data['ville_evenement']
            except:
                event_details.ville_evenement = ""

            try:
                event_details.code_postal_evenement=data['code_postal_evenement']
            except:
                event_details.code_postal_evenement = 77176

            event_details.save()

            event_product = EventProduct()
            try:
                event_product.photobooth = data['photobooth']
            except:
                event_product.photobooth = False
            try:
                event_product.miroirbooth = data['miroirbooth']
            except:
                event_product.miroirbooth = False
            try:
                event_product.videobooth = data['videobooth']
            except:
                event_product.videobooth = False

            event_product.save()

            event_option = EventOption()
            try:
                event_option.mur_floral = data['mur_floral']
            except:
                event_option.mur_floral = False
            try:
                event_option.phonebooth = data['phonebooth']
            except:
                event_option.phonebooth = False
            try:
                event_option.livreor = data['livreor']
            except:
                event_option.livreor = False
            try:
                event_option.magnets = data['magnets']
            except:
                event_option.magnets = False
            try:
                event_option.duree = data['duree']
            except:
                event_option.duree = 5
            event_option.save()

            event = Event(
                client=client,
                event_details=event_details,
                event_product=event_product,
                event_option=event_option,
                prix_brut=data['prix_brut'],
                reduc_all=data['reduc_all'],
                prix_proposed=data['prix_proposed'],
                prix_valided=data['prix_valided'],
                status=data['status'],
            )
            event.save()
            client = Client.objects.get(nom=data['nom'])
            try:
                date = data['created_at'].split("-")
                naive_datetime = datetime(int(date[0]), int(date[1]), int(date[2]))  # Exemple de datetime naïve
                aware_datetime = make_aware(naive_datetime)
                Event.objects.filter(client=client).update(created_at=aware_datetime)

            except:
                date = data['signer_at'].split("-")
                naive_datetime = datetime(int(date[0]), int(date[1]), int(date[2]))  # Exemple de datetime naïve
                aware_datetime = make_aware(naive_datetime)
                Event.objects.filter(client=client).update(created_at=aware_datetime)
            try:
                date_sign = data['signer_at'].split("-")
                naive_datetime_sign = datetime(int(date_sign[0]), int(date_sign[1]), int(date_sign[2]))  # Exemple de datetime naïve
                aware_datetime_sign = make_aware(naive_datetime_sign)
                Event.objects.filter(client=client).update(signer_at=aware_datetime_sign)
            except:pass

        if Client.objects.filter(nom=nom).exists():
            i+=1


    print(str(i) + " / " + str(len(event_presta)))