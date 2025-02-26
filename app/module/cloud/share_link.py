
from datetime import datetime, timedelta

from app.module.cloud.get_pcloud_data import get_pcloud_event_folder_data
from myselfiebooth.settings import API_PCLOUD_URL, ACCESS_TOKEN
import requests

MAX_DOWNLOADS = 10  # Nombre maximal de téléchargements
MAX_TRAFFIC = 10000 * 1024 * 1024  # 10000 Mo en octets
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