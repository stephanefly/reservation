import unicodedata
import re
import requests
from datetime import datetime

from app.module.cloud.get_pcloud_data import get_pcloud_event_folder_data
from myselfiebooth.settings import API_PCLOUD_URL, ACCESS_TOKEN


def normalize_name(event):
    # Vérification et conversion de la date en datetime si c'est une chaîne
    if isinstance(event.event_details.date_evenement, str):
        date_evenement = datetime.strptime(event.event_details.date_evenement, '%Y-%m-%d')  # Adaptation du format
    else:
        date_evenement = event.event_details.date_evenement

    # Création du nom de répertoire
    directory_name = date_evenement.strftime('%Y-%m-%d') + '_' + str(event.client.nom).upper()
    normalized_name = unicodedata.normalize('NFKD', directory_name).encode('ASCII', 'ignore').decode('utf-8')
    normalized_name = re.sub(r'\s+', '-', normalized_name)

    return normalized_name

def rename_pcloud_event_folder(old_directory_name, new_directory_name, prepa: bool = False):
    """
    Renomme un dossier pCloud à partir de son ancien nom.
    """
    folder_data = get_pcloud_event_folder_data(old_directory_name, prepa)
    if not folder_data:
        return False

    url = f"{API_PCLOUD_URL}/renamefolder"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_data["folderid"],
        'toname': new_directory_name
    }

    response = requests.get(url, params=params, timeout=(3.05, 12))
    response.raise_for_status()
    return response.json().get("result") in (0, 2004)


def rennaming_pcloud_event_folder(event, new_directory_name, prepa: bool = False):
    """Compatibilité avec les appels existants qui transmettent un Event."""
    return rename_pcloud_event_folder(
        event.event_template.directory_name,
        new_directory_name,
        prepa=prepa,
    )
