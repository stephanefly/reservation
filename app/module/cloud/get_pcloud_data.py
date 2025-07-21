import os
import json
import requests

from myselfiebooth.settings import API_PCLOUD_URL, ROOT_FOLDER_ID, ACCESS_TOKEN, ROOT_FOLDER_PREPA_ID, \
    ROOT_FOLDER_MONTAGE_2025, ROOT_FOLDER_MONTAGE_2026


def get_pcloud_event_folder_data(event_name, prepa: bool = False):
    """
    Retrieve the folder ID from pCloud by event name.
    """
    url = f"{API_PCLOUD_URL}/listfolder"

    folder_id = ROOT_FOLDER_PREPA_ID if prepa else ROOT_FOLDER_ID
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_id
    }

    response = requests.post(url, params=params)
    data = response.json()

    for folder_data in data["metadata"]["contents"]:
        if folder_data["name"] == event_name:
            return folder_data


def create_pcloud_event_folder(event, prepa: bool = False, montage: bool = False):
    """
    Create a folder on the pCloud server, either in the standard event folder or in the preparation folder.

    Args:
        event: L'objet événement contenant un template avec un nom de dossier.
        prepa (bool): Si True, crée le dossier dans le dossier 'préparation'. Sinon, dans le dossier principal.

    Returns:
        bool: True si succès ou dossier déjà existant, False sinon.
    """
    url = f"{API_PCLOUD_URL}/createfolder"
    folder_client_name = event.event_template.directory_name

    # Détermination de l'ID parent selon les options
    if montage:
        if folder_client_name[:4] == "2025":
            parent_folder_id = ROOT_FOLDER_MONTAGE_2025
        else:
            parent_folder_id = ROOT_FOLDER_MONTAGE_2026
    elif prepa:
        parent_folder_id = ROOT_FOLDER_PREPA_ID
    else:
        parent_folder_id = ROOT_FOLDER_ID

    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': parent_folder_id,
        'name': folder_client_name,
    }

    response = requests.post(url, params=params)

    if response.status_code != 200:
        return False  # Échec de la requête

    data = response.json()

    # Vérifier si le dossier a été créé ou existe déjà
    if data["result"] == 0 or data["result"] == 2004:
        return True

    return False  # Échec si le dossier n'existe pas et n'a pas été créé


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
