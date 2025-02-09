import os
import json
import requests

from myselfiebooth.settings import API_PCLOUD_URL, ROOT_FOLDER_ID, ACCESS_TOKEN


def get_pcloud_event_folder_data(event_name: str) -> dict:
    """
    Retrieve the folder ID from pCloud by event name.
    """
    url = f"{API_PCLOUD_URL}/listfolder"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': ROOT_FOLDER_ID
    }

    response = requests.post(url, params=params)
    data = response.json()

    for folder_data in data["metadata"]["contents"]:
        if folder_data["name"] == event_name:
            return folder_data


def create_pcloud_event_folder(event):
    """
    Create a folder on the pCloud server.
    """
    url = f"{API_PCLOUD_URL}/createfolder"
    folder_client_name = event.event_template.directory_name
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': ROOT_FOLDER_ID,
        'name': folder_client_name,
    }

    response = requests.get(url, params=params)
    data = response.json()  # Parse the JSON response
    if data["result"] == 2004:
        return True

    # Ensure the 'metadata' key exists and contains 'contents'
    elif 'metadata' in data and 'contents' in data['metadata']:
        for item in data['metadata']['contents']:
            if item.get('name') == folder_client_name and item.get('isfolder'):
                return True

    # If no matching folder is found
    return False


def find_pcloud_empty_folder(folder_data: dict):
    """
    Supprime les dossiers vides ou les dossiers appelés 'thumb' dans un répertoire pCloud donné.

    Args:
        folder_data (dict): Dictionnaire contenant au minimum l'ID du dossier (folderid).
    """
    url = f"{API_PCLOUD_URL}/listfolder"
    params = {'access_token': ACCESS_TOKEN, 'folderid': folder_data["folderid"]}

    # Récupération des métadonnées du dossier
    response = requests.get(url, params=params)
    data = response.json()

    # Vérifier le contenu du dossier
    contents = data.get("metadata", {}).get("contents", [])
    for subfolder_data in contents:
        if subfolder_data.get("isfolder"):  # Vérifie si c'est un sous-dossier
            find_pcloud_empty_folder(subfolder_data)

    if not contents:  # Si le dossier est vide
        delete_pcloud_empty_folder(folder_data)


def delete_pcloud_empty_folder(folder_data: dict):
    delete_url = f"{API_PCLOUD_URL}/deletefolder"
    delete_params = {'access_token': ACCESS_TOKEN, 'folderid': folder_data["folderid"]}
    requests.get(delete_url, params=delete_params)
