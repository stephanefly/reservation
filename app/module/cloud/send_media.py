import os
import cv2


def check_media_to_send(event):

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

    return folder_to_send
