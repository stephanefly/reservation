import os
import json
import requests
import cv2
import numpy as np

from myselfiebooth.settings import API_PCLOUD_URL, ACCESS_TOKEN


def get_pcloud_print_folder(folder_data: dict):
    """
    Fetch all image file links from a pCloud folder.
    """

    url = f"{API_PCLOUD_URL}/listfolder"
    params = {'access_token': ACCESS_TOKEN, 'folderid': folder_data["folderid"]}

    response = requests.get(url, params=params)
    data = response.json()

    for subfolder_data in data.get("metadata", {}).get("contents", []):
        if subfolder_data.get("name") == "Prints":
            params = {'access_token': ACCESS_TOKEN, 'folderid': subfolder_data.get("folderid")}

            response = requests.get(url, params=params)
            print_folder_data = response.json()
            return print_folder_data


def fetch_pcloud_prints(print_folder_data: dict):
    # Collect file links for images
    lst_image_links = []
    for file in print_folder_data.get("metadata", {}).get("contents", []):
        if file["isfolder"] == 0 and file["name"].lower().endswith(('.jpg', '.jpeg', '.png')):
            file_url = f"{API_PCLOUD_URL}/getfilelink"
            file_params = {'access_token': ACCESS_TOKEN, 'fileid': file["fileid"]}

            file_response = requests.get(file_url, params=file_params)
            if file_response.status_code == 200:
                file_data = file_response.json()
                file_link = file_data["hosts"][0] + file_data["path"]

                # Ensure the URL starts with "https://"
                if not file_link.startswith("http"):
                    file_link = "https://" + file_link.lstrip("/")

                lst_image_links.append(file_link)
    return lst_image_links


def create_timelapse_from_pcloud(image_links: list, output_file: str, fps: int = 10):
    """
    Create a timelapse video from images in a pCloud folder without downloading them.
    """

    # Initialize the video writer after getting the first frame
    first_frame_data = requests.get(image_links[0]).content
    first_frame = cv2.imdecode(np.frombuffer(first_frame_data, np.uint8), cv2.IMREAD_COLOR)
    height, width, _ = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # Process all images
    for image_link in image_links:
        image_data = requests.get(image_link).content
        frame = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue
        video_writer.write(frame)

    video_writer.release()


def upload_file_to_pcloud(file_path: str, folder_data: dict):
    """
    Upload a file to a specific pCloud folder.
    """
    url = f"{API_PCLOUD_URL}/uploadfile"
    params = {'access_token': ACCESS_TOKEN, 'folderid': folder_data['folderid']}

    with open(file_path, "rb") as f:
        files = {'file': f}
        response = requests.post(url, params=params, files=files)


def delete_local_file(file_path: str):
    """
    Delete a local file if it exists.
    """
    if os.path.exists(file_path):
        os.remove(file_path)


def create_timelaps(event, folder_data: dict, print_folder_data):

    # List Image Links
    lst_image_links = fetch_pcloud_prints(print_folder_data)

    # Create the timelapse video
    output_video_file = f"{event.event_template.directory_name}-timelapse.mp4"
    create_timelapse_from_pcloud(lst_image_links, output_video_file, fps=10)

    # Upload the video to pCloud
    upload_file_to_pcloud(output_video_file, folder_data)

    # Delete the local video file after upload
    delete_local_file(output_video_file)