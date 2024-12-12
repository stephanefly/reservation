import os
import json
import requests

from myselfiebooth.settings import API_PCLOUD_URL, ROOT_FOLDER_ID, ACCESS_TOKEN


def get_pcloud_event_folder_data(event_name: str) -> dict:
    """
    Retrieve the folder ID from pCloud by event name.
    """
    url = f"{API_PCLOUD_URL}/listfolder"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': ROOT_FOLDER_ID
    }

    response = requests.get(url, params=params)
    data = response.json()

    for folder_data in data["metadata"]["contents"]:
        if folder_data["name"] == event_name:
            return folder_data


def get_pcloud_link_event_folder(folder_data: dict) -> str:
    """
    Retrieve the public link for a folder by its ID.
    """
    url = f"{API_PCLOUD_URL}/getfolderpublink"
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': folder_data["folderid"]
    }

    response = requests.get(url, params=params)
    link_event_folder = response.json()["link"]
    return link_event_folder

