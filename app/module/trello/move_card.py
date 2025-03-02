
from app.module.trello.get_trello_data import get_data_card_by_name
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO

import requests

# Assurez-vous que KEY_TRELLO et TOKEN_TRELLO sont définis quelque part dans votre code

def move_card_to_list(event, list_id):
    """
    Déplace une carte Trello vers une liste spécifiée en fonction de l'événement.

    :param event: Un objet événement contenant au moins un attribut 'nom' pour identifier la carte.
    :param list_id: L'ID de la liste cible où la carte doit être déplacée.
    """
    # Fonction pour obtenir l'ID de la carte basée sur le nom de l'événement

    card_id = get_data_card_by_name(event.client.nom)["id"]

    # URL de l'API pour déplacer une carte
    url = f"https://api.trello.com/1/cards/{card_id}"

    # Paramètres de la requête
    params = {
        'key': KEY_TRELLO,
        'token': TOKEN_TRELLO,
        'idList': list_id,  # ID de la liste cible
    }

    # Effectuer la requête pour déplacer la carte
    response = requests.put(url, params=params)

    # Vérifier si la requête a réussi
    if response.status_code == 200:
        print("La carte a été déplacée avec succès dans la liste :", list_id)
        return True
    else:
        print("Erreur lors du déplacement de la carte :", response.text)
        return False


# Exemples d'utilisation
def to_acompte_ok(event):
    # ID de la liste "Acompte OK"
    if move_card_to_list(event, '63c721825a499b0147a55b68'):
        return True
    else:
        return False

def to_refused(event):
    if move_card_to_list(event, '63c72153d70f3f04062df9d4'):  # ID de la liste pour les cartes refusées
        return True
    else:
        return False

def to_list_devis_fait(event):
    if move_card_to_list(event, '65c6aecbe90021ebb7b9595b'):  # AUTO-ENVOI
        return True
    else:
        return False