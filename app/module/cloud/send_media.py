import os
import cv2


def create_timelapse(name, input_folder, dossier_to_send, fps=10):

    image_files = sorted([f for f in os.listdir(input_folder) if f.endswith(('.jpg', '.jpeg', '.png'))])

    if len(image_files) == 0:
        print("Aucune image trouvée dans le répertoire spécifié.")
        return

    image_path = os.path.join(input_folder, image_files[0])
    img = cv2.imread(image_path)
    height, width, _ = img.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Format de compression pour le fichier vidéo
    output_file = os.path.join(dossier_to_send, str(name) + "-timelaps.mp4")
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    for image_file in image_files:
        image_path = os.path.join(input_folder, image_file)
        img = cv2.imread(image_path)
        out.write(img)

    out.release()
    print("Timelapse créé avec succès : {}".format(output_file))

    return True


def complete_and_check_media(event):

    # reference_folder_or_file = ["Prints", "360", "AUDIO PHONEBOOTH", "timelaps", "VOGUE", "IPADBOOTH"]
    path_folder = os.path.join(r"P:\CLIENT-EVENT", event.event_template.directory_name)

    folder_to_send = []
    if ("photobooth" in event.event_product.get_selected_booths() or
            "miroirbooth" in event.event_product.get_selected_booths()):
        folder_to_send.append("Prints")
        input_folder = os.path.join(path_folder, "Prints")
        if create_timelapse(event.event_template.directory_name, input_folder, path_folder, fps=10):
            folder_to_send.append(f"{event.event_template.directory_name}-timelaps.mp4")

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
