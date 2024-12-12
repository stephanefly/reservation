import unicodedata
import re
import requests
import unicodedata
import re
from datetime import datetime

from app.module.cloud.get_pcloud_data import get_pcloud_event_folder_data
from myselfiebooth.settings import API_PCLOUD_URL, ROOT_FOLDER_ID, ACCESS_TOKEN


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

def rennaming_pcloud_event_folder(event, new_directory_name):
    """
    Renname a folder on the pCloud server.
    """
    folder_data = get_pcloud_event_folder_data(event.event_template.directory_name)

    url = f"{API_PCLOUD_URL}/renamefolder"
    folder_client_name = event.event_template.directory_name
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_data["folderid"],
        'toname': new_directory_name
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
