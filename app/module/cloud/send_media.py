from django.shortcuts import get_object_or_404, redirect

from app.models import Event
from app.module.cloud.create_timelaps import get_pcloud_print_folder, create_timelaps
from app.module.cloud.get_pcloud_data import get_pcloud_event_folder_data, find_pcloud_empty_folder
from app.module.cloud.share_link import get_pcloud_link_event_folder
from app.module.mail.send_mail_event import send_mail_event


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


def send_media_logic(event_id):

    event = get_object_or_404(Event, pk=event_id)

    folder_to_send = check_media_to_send(event)
    folder_data = get_pcloud_event_folder_data(event.event_template.directory_name)

    if "Prints" in folder_to_send:
        print_folder_data = get_pcloud_print_folder(folder_data)
        create_timelaps(event, folder_data, print_folder_data)

    if not event.event_post_presta.link_media_shared:
        event.event_post_presta.link_media_shared = get_pcloud_link_event_folder(folder_data)
        event.event_post_presta.save()

    send_mail_event(event, 'send_media')

    find_pcloud_empty_folder(folder_data)
    event.event_post_presta.sent = True
    event.event_post_presta.save()
    event.status = 'Sent Media'
    event.save()
