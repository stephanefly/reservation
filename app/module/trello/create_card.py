import requests
import json
from datetime import datetime

from app.module.trello.get_trello_data import get_id_label
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


def create_card(post_data):

   data = get_data_card(post_data)

   url = "https://api.trello.com/1/cards"

   idList_auto_devis = '65be53f99ba9e7ddeaa3b88f'
   query = {
      'idList': idList_auto_devis,
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   query.update(data)

   response = requests.request(
      "POST",
      url,
      params=query
   )

   print(response.text)

def get_data_card(post_data):

   data = {}

   client_data = post_data['client']
   event_data = post_data['event']
   product_data = post_data['product']
   options_data = post_data['options']

   data['name'] = client_data["prenom"] + " " + client_data["nom"]
   data['due'] = datetime.strptime(event_data["date"], '%Y-%m-%d')
   data['des'] = str(post_data)

   # Label : PRODUIT, DUREE, HOW_FIND, CODE POSTAL, option
   data['idLabels'] = []

   # PRODUIT
   products = product_data.split(",")
   for product in products:
      label_id = get_id_label(product.strip())
      if label_id:
         data['idLabels'].append(label_id)

   # DUREE
   if options_data['heure_range']:
      duree = str(options_data['heure_range']) +'h'
      data['idLabels'].append(get_id_label(duree))
   else:
      data['idLabels'].append(get_id_label("LOCATION"))
      pass

   # CODE POSTAL
   departement = event_data['code_postal'].strip()[:2]
   data['idLabels'].append(get_id_label(departement))

   # HOW_FIND
   data['idLabels'].append(get_id_label(client_data['how_find']))

   # OPTION
   if options_data['murfloral']==1:
      data['idLabels'].append(get_id_label("Mur Floral"))
   if options_data['phonebooth'] == 1:
      data['idLabels'].append(get_id_label("Phonebooth"))
   if options_data['magnets_range']:
      data['idLabels'].append(get_id_label("Magnets"))

   print(data)

   return data
