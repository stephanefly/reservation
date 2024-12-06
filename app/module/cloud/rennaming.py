import unicodedata
import re

import unicodedata
import re
from datetime import datetime


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


