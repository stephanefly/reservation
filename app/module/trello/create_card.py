import requests
from datetime import datetime

from app.module.trello.get_trello_data import get_id_label, get_lst_labels, TRELLO_TIMEOUT
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


def create_card(post_data):

   data = data_to_post_on_card(post_data)

   url = "https://api.trello.com/1/cards"

   idList_auto_devis = '65be53f99ba9e7ddeaa3b88f'
   query = {
      'idList': idList_auto_devis,
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   query.update(data)

   response = requests.post(
      url,
      params=query,
      timeout=TRELLO_TIMEOUT,
   )
   response.raise_for_status()
   return response.json()["id"]

def data_to_post_on_card(post_data):

   data = {}

   client_data = post_data['page_client']
   event_data = post_data['event']
   product_data = post_data['product']
   options_data = post_data['options']

   data['name'] = client_data["nom"]
   data['due'] = datetime.strptime(event_data["date"], '%Y-%m-%d')

   # DESCRIPTION
   adresse = ""
   for key, value in post_data['event'].items():
      adresse += str(value) + str(" - ")
   data['desc'] = adresse

   # Label : PRODUIT, DUREE, HOW_FIND, CODE POSTAL, option, ENTREPIRSE
   data['idLabels'] = []
   labels = get_lst_labels()  # Un seul appel Trello pour les étiquettes

   def add_label(name):
      label_id = get_id_label(name, labels=labels)
      if label_id and label_id not in data['idLabels']:
         data['idLabels'].append(label_id)

   # PRODUIT
   products = product_data.split(",")
   for product in products:
      add_label(product.strip())

   # DUREE
   if post_data['heure_range']:
      duree = str(post_data['heure_range']) +'h'
      add_label(duree)
   else:
      add_label("LOCATION")

   # CODE POSTAL
   departement = event_data['code_postal'].strip()[:2]
   add_label(departement)

   # HOW_FIND
   add_label(client_data['how_find'])

   # OPTION
   options = options_data.split(",")
   for option in options:
      add_label(option.strip())

   if post_data['magnets_range'] != 0 or post_data['PorteCles_range']!= 0 or post_data['MagnetsSimple_range']!= 0:
      add_label("Magnets")

   # ENTREPRISE
   if client_data['raison_sociale']:
      add_label('ENTREPRISE')

   return data
