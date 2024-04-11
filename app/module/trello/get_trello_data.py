import requests
import json
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


# https://api.trello.com/1/boards/bm6IDBqY/cards?key=29e7594c82a72b2ee23f23926ad2308a&token=c9df6b2f0b980a240ef4d936489446f0af8da51e99c2672fed693a97359be972
# https://api.trello.com/1/boards/bm6IDBqY/lists?key=29e7594c82a72b2ee23f23926ad2308a&token=c9df6b2f0b980a240ef4d936489446f0af8da51e99c2672fed693a97359be972
# https://api.trello.com/1/boards/bm6IDBqY/labels?key=29e7594c82a72b2ee23f23926ad2308a&token=c9df6b2f0b980a240ef4d936489446f0af8da51e99c2672fed693a97359be972

def get_lst_labels():
   url = "http://api.trello.com/1/board/bm6IDBqY/labels"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   response = requests.request(
      "GET",
      url,
      params=query
   )

   lst_labels = json.loads(response.text)
   return lst_labels


def get_lst_listes():
   url = "http://api.trello.com/1/board/bm6IDBqY/lists"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   response = requests.request(
      "GET",
      url,
      params=query
   )

   lst_listes = json.loads(response.text)

   return lst_listes


def get_lst_cards():

   url = "https://api.trello.com/1/board/bm6IDBqY/cards"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   response = requests.request(
      "GET",
      url,
      params=query,
   )


   lst_cards = json.loads(response.text)
   return lst_cards


def get_id_label(post_label):
   # Supposons que get_lst_labels() renvoie une liste de labels sous forme de dictionnaires
   for label in get_lst_labels():
      if label['name'] == post_label:
         return label['id']  # Retourner l'ID dès qu'une correspondance est trouvée


def get_data_card_by_name(name):
   for card_json in get_lst_cards():
      if card_json['name'] == name:
         return card_json

def get_prio_card_name():

   # PRIO : "idList": "617aa17f82103360510559e2",
   url = "https://api.trello.com/1/lists/617aa17f82103360510559e2/cards"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   response = requests.request(
      "GET",
      url,
      params=query
   )

   lst_cards = json.loads(response.text)
   return lst_cards

def get_all_card():
   url = "https://api.trello.com/1/boards/bm6IDBqY/cards"

   query = {
      'key': KEY_TRELLO,
      'token': TOKEN_TRELLO,
   }

   response = requests.request(
      "GET",
      url,
      params=query
   )

   all_trello_cards = json.loads(response.text)
   return all_trello_cards