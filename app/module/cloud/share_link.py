
from datetime import datetime, timedelta

from myselfiebooth.settings import API_PCLOUD_URL, ACCESS_TOKEN
import requests

MAX_DOWNLOADS = 100  # Nombre maximal de téléchargements
MAX_TRAFFIC = 100000 * 1024 * 1024  # 100000 Mo en octets
EXPIRE_DAYS = 45 # Nombre de jours avant expiration
expire_datetime = datetime.utcnow() + timedelta(days=EXPIRE_DAYS)


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
    folder_data = get_pcloud_event_folder_data(event.event_template.directory_name)
    event.event_template.link_media_shared = get_pcloud_link_event_folder(folder_data)
    event.event_template.save()
    event.save()

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
