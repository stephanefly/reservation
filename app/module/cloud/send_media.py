import os
import cv2


def complete_and_check_media(event):

    # reference_folder_or_file = ["Prints", "360", "AUDIO PHONEBOOTH", "timelaps", "VOGUE", "IPADBOOTH"]
    path_folder = os.path.join(r"P:\CLIENT-EVENT", event.event_template.directory_name)

    folder_to_send = []
    if ("photobooth" in event.event_product.get_selected_booths() or
            "miroirbooth" in event.event_product.get_selected_booths()):
        folder_to_send.append("Prints")

    if ("videobooth" in event.event_product.get_selected_booths() or
            "airbooth" in event.event_product.get_selected_booths()):
        folder_to_send.append("360")

    if "voguebooth" in event.event_product.get_selected_booths():
        folder_to_send.append("VOGUE")

    if "ipadbooth" in event.event_product.get_selected_booths():
        folder_to_send.append("IPADBOOTH")

    if event.event_option.Phonebooth:
        folder_to_send.append("AUDIO PHONEBOOTH")

    folder_in_directory = os.listdir(path_folder)
    missing_folders = [folder for folder in folder_to_send if folder not in folder_in_directory]

    if missing_folders:
        event.event_details.comment = f"Missing folders: {', '.join(missing_folders)}"
        event.event_details.save()
        return False
    return True
