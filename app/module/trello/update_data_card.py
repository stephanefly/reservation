from datetime import datetime

import requests

from app.module.trello.get_trello_data import (
    TRELLO_TIMEOUT,
    get_data_card_by_name,
    get_lst_labels,
)
from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


def update_option_labels_trello(event, data_card=None):
    data_card = data_card or get_data_card_by_name(event.client.nom)
    if not data_card:
        return False

    # Les labels hors options (tous ceux qui ne sont pas bleus) sont conservés.
    label_ids = [
        label["id"]
        for label in data_card["labels"]
        if label["color"] != "blue"
    ]

    # Une seule lecture de la liste Trello, au lieu d'une lecture par option active.
    labels_by_name = {label["name"]: label["id"] for label in get_lst_labels()}
    active_options = [
        option_name
        for option_name in (
            "MurFloral",
            "Phonebooth",
            "LivreOr",
            "Fond360",
            "PanneauBienvenue",
            "Holo3D",
            "PanneauFontaine",
            "VideoLivreOr",
        )
        if getattr(event.event_option, option_name)
    ]
    if event.event_option.magnets or event.event_option.PorteCles or event.event_option.MagnetsSimple:
        active_options.append("Magnets")

    label_ids.extend(
        labels_by_name[option_name]
        for option_name in active_options
        if option_name in labels_by_name
    )
    label_ids = list(dict.fromkeys(label_id for label_id in label_ids if label_id))

    response = requests.put(
        f"https://api.trello.com/1/cards/{data_card['id']}/idLabels",
        params={
            "key": KEY_TRELLO,
            "token": TOKEN_TRELLO,
            "value": ",".join(label_ids),
        },
        timeout=TRELLO_TIMEOUT,
    )
    return response.status_code == 200


def update_trello_date(event, data_card=None):
    data_card = data_card or get_data_card_by_name(event.client.nom)
    if not data_card:
        return False

    due_date_obj = event.event_details.date_evenement
    if isinstance(due_date_obj, str):
        due_date_obj = datetime.strptime(due_date_obj, "%Y-%m-%d")

    response = requests.put(
        f"https://api.trello.com/1/cards/{data_card['id']}",
        params={
            "key": KEY_TRELLO,
            "token": TOKEN_TRELLO,
            "due": due_date_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        },
        timeout=TRELLO_TIMEOUT,
    )
    return response.status_code == 200
