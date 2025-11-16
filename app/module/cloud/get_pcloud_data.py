from app.models import EventPostPrestation
from myselfiebooth.settings import API_PCLOUD_URL, ROOT_FOLDER_ID, ACCESS_TOKEN, ROOT_FOLDER_PREPA_ID, \
    ROOT_FOLDER_MONTAGE_2025, ROOT_FOLDER_MONTAGE_2026
from datetime import datetime, timedelta
import requests

MAX_DOWNLOADS = 100  # Nombre maximal de téléchargements
MAX_TRAFFIC = 100000 * 1024 * 1024  # 100000 Mo en octets
EXPIRE_DAYS = 45 # Nombre de jours avant expiration
expire_datetime = datetime.utcnow() + timedelta(days=EXPIRE_DAYS)

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
        folder_data = get_pcloud_event_folder_data(folder_client_name)
        event.event_post_presta.link_media_shared = get_pcloud_link_event_folder(folder_data)
        event.event_post_presta.save()
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



def get_pcloud_link_event_folder(folder_data: dict) -> str:
    """
    Retrieve the public link for a folder by its ID.
    """
    url = f"{API_PCLOUD_URL}/getfolderpublink"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_data["folderid"],
        'expire': expire_datetime,
        'maxdownloads': MAX_DOWNLOADS,
        'maxtraffic': MAX_TRAFFIC,
    }

    response = requests.get(url, params=params)
    link_event_folder = response.json()["link"]
    return link_event_folder


def create_link_event_folder(event):
    """
    Génère et sauvegarde le lien public du dossier pCloud
    pour cet event uniquement. Crée event_post_presta si absent.
    """

    # 1) Récupérer ou créer l'objet post-presta
    post = event.event_post_presta

    if post is None:
        print(f"[pCloud] Aucun post-presta pour event {event.id} → création automatique")
        post = EventPostPrestation.objects.create(event=event)
        event.event_post_presta = post
        event.save(update_fields=["event_post_presta"])

    # 2) Récupération du dossier pCloud
    folder_name = event.event_template.directory_name
    folder_data = get_pcloud_event_folder_data(folder_name)

    if not folder_data:
        print(f"[pCloud] Dossier introuvable pour event {event.id}")
        return False

    # 3) Génération du lien public
    link = get_pcloud_link_event_folder(folder_data)

    # 4) Sauvegarde dans le post-presta
    if not post.link_media_shared:
        post.link_media_shared = link
        post.save(update_fields=["link_media_shared"])
        print(f"[pCloud] Lien enregistré pour event {event.id}")
    else:
        print(f"[pCloud] Lien déjà existant pour event {event.id}")

    return True




def upload_template_to_pcloud(event, uploaded_file, folder_data: dict):
    """
    Upload an in-memory file (e.g., from a Django form) to a specific pCloud folder.
    """
    url = f"{API_PCLOUD_URL}/uploadfile"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_data['folderid']
    }

    increment = event.event_template.num_template
    image_name = f"MySelfieBooth-{event.event_template.directory_name}-{increment}.png"
    event.event_template.image_name = image_name
    event.event_template.num_template += 1
    event.event_template.save()

    files = {
        'file': (image_name, uploaded_file.file, uploaded_file.content_type)
    }

    response = requests.post(url, params=params, files=files)

    if response.status_code == 200:
        event.event_template.url_pcloud_template_folder = get_pcloud_link_event_folder(folder_data)
        event.event_template.save()
        event.save()
        return response.json()
    else:
        return None


def get_public_image_link_from_path(path: str) -> str:
    """
    Retourne l'URL publique directe d'une image stockée à un chemin précis sur pCloud.
    """
    url = f"{API_PCLOUD_URL}/getfilelink"
    params = {
        "access_token": ACCESS_TOKEN,
        "path": path,
        "contenttype": "image/png"
    }
    response = requests.get(url, params=params)
    data = response.json()

    http_url = f"https://{data['hosts'][0]}{data['path']}"

    return http_url
