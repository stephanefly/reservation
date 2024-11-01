import unicodedata
import re

import unicodedata
import re
from datetime import datetime


def normalized_directory_name(event):
    # Vérification et conversion de la date en datetime si c'est une chaîne
    if isinstance(event.event_details.date_evenement, str):
        date_evenement = datetime.strptime(event.event_details.date_evenement, '%Y-%m-%d')  # Adaptation du format
    else:
        date_evenement = event.event_details.date_evenement

    # Création du nom de répertoire
    directory_name = date_evenement.strftime('%Y%m%d') + '-' + str(event.client.nom).upper()
    normalized_directory_name = unicodedata.normalize('NFKD', directory_name).encode('ASCII', 'ignore').decode('utf-8')
    normalized_directory_name = re.sub(r'\s+', '_', normalized_directory_name)

    return normalized_directory_name
