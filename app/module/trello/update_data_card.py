import requests
from datetime import datetime
from app.module.trello.get_trello_data import get_id_label, get_data_card_by_name
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


def update_option_labels_trello(event):

   data_card = get_data_card_by_name(event.client.nom)

   label_ids= []

   for label in data_card["labels"]:
      if label['color'] != 'blue':
         label_ids.append(label['id'])

   if event.event_option.MurFloral:
      label_ids.append(get_id_label("MurFloral"))
   if event.event_option.Phonebooth:
      label_ids.append(get_id_label("Phonebooth"))
   if event.event_option.LivreOr:
      label_ids.append(get_id_label("LivreOr"))
   if event.event_option.Fond360:
      label_ids.append(get_id_label("Fond360"))
   if event.event_option.PanneauBienvenue:
      label_ids.append(get_id_label("PanneauBienvenue"))
   if event.event_option.Holo3D:
      label_ids.append(get_id_label("Holo3D"))
   if event.event_option.PanneauFontaine:
       label_ids.append(get_id_label("PanneauFontaine"))
   if event.event_option.VideoLivreOr:
       label_ids.append(get_id_label("VideoLivreOr"))
   if event.event_option.magnets != "0":
      label_ids.append(get_id_label("Magnets"))

   # Convertir la liste des ID d'étiquettes en une chaîne séparée par des virgules
   label_ids_str = ','.join(label_ids)

   card_id = data_card["id"]
   url = f"https://api.trello.com/1/cards/{card_id}/idLabels"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
      'value': label_ids_str  # Pour mettre à jour les étiquettes, utilisez cette clé avec les ID des étiquettes
   }

   response = requests.put(
      url,
      params=query
   )


   # Vérifier si la requête a réussi
   if response.status_code == 200:
      print("Carte Mise à Jours")
   else:
      print("Erreur lors Mise à Jours de la carte :", response.text)


def update_trello_date(event):
   data_card = get_data_card_by_name(event.client.nom)

   card_id = data_card["id"]
   url = f"https://api.trello.com/1/cards/{card_id}"

   # Conversion de la date en objet datetime si nécessaire
   if isinstance(event.event_details.date_evenement, str):
      due_date_obj = datetime.strptime(event.event_details.date_evenement, '%Y-%m-%d')
   else:
      due_date_obj = event.event_details.date_evenement

   # Convertir la date en format ISO 8601 pour Trello
   due_date = due_date_obj.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
      'due': due_date
   }

   response = requests.put(
      url,
      params=query
   )

   # Vérifier si la requête a réussi
   if response.status_code == 200:
      print("Carte Mise à Jours")
   else:
      print("Erreur lors Mise à Jours de la carte :", response.text)
