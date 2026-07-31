import requests

from myselfiebooth.settings import KEY_TRELLO, TOKEN_TRELLO


BOARD_ID = "bm6IDBqY"
TRELLO_TIMEOUT = (3.05, 10)
SPECIAL_LABEL_IDS = {
    "360Airbooth": "669591d56535a9bb2e8a60bd",
    "Voguebooth": "669591939c9d96fbe5d218c2",
    "Ipadbooth": "669591e13475d95a06c61737",
}


def _get_json(url):
    response = requests.get(
        url,
        params={"key": KEY_TRELLO, "token": TOKEN_TRELLO},
        timeout=TRELLO_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_lst_labels():
    return _get_json(f"https://api.trello.com/1/boards/{BOARD_ID}/labels")


def get_lst_listes():
    return _get_json(f"https://api.trello.com/1/boards/{BOARD_ID}/lists")


def get_lst_cards():
    return _get_json(f"https://api.trello.com/1/boards/{BOARD_ID}/cards")


def get_id_label(post_label, labels=None):
    if post_label in SPECIAL_LABEL_IDS:
        return SPECIAL_LABEL_IDS[post_label]

    labels = labels if labels is not None else get_lst_labels()
    for label in labels:
        if label["name"] == post_label:
            return label["id"]
    return None


def get_data_card_by_name(name, cards=None):
    cards = cards if cards is not None else get_lst_cards()
    for card_json in cards:
        if card_json["name"] == name:
            return card_json
    return None


def get_prio_card_name():
    return _get_json("https://api.trello.com/1/lists/617aa17f82103360510559e2/cards")


def get_all_card():
    return get_lst_cards()
