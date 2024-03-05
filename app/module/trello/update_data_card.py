import requests

from app.module.trello.create_card import get_data_card
from app.module.trello.get_trello_data import get_id_card, get_id_label
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


def update_data_trello(event):

   data_card = get_data_card(event.client.nom)

   label_ids= []

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
   if event.event_option.magnets != 0:
      label_ids.append(get_id_label("magnets"))

   # Convertir la liste des ID d'étiquettes en une chaîne séparée par des virgules
   label_ids_str = ','.join(label_ids)

   card_id = data_card["id"]
   url = f"https://api.trello.com/1/cards/{card_id}/idLabels"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
      'value': label_ids_str  # Pour mettre à jour les étiquettes, utilisez cette clé avec les ID des étiquettes
   }

   response = requests.request(
      "POST",
      url,
      params=query
   )

