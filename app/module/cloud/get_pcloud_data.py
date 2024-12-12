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

    response = requests.post(url, params=params)
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


def create_pcloud_event_folder(event):
    """
    Create a folder on the pCloud server.
    """
    url = f"{API_PCLOUD_URL}/createfolder"
    folder_client_name = event.event_template.directory_name
    params = {
        'access_token': ACCESS_TOKEN,
        'folderid': ROOT_FOLDER_ID,
        'name': folder_client_name,
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

    # If no matching folder is found
    return False


