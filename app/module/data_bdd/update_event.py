from app.module.cloud.get_pcloud_data import create_pcloud_event_folder
from app.module.devis_pdf.make_table import calcul_prix_distance
from app.module.espace_client.data_client import generate_code_espace_client
from app.module.cloud.rennaming import normalize_name, rennaming_pcloud_event_folder
from django.utils.timezone import now
from app.models import EventTemplate, EventAcompte
from app.module.mail.send_mail_event import send_mail_event
from app.module.trello.move_card import to_acompte_ok

from django.db import transaction
from django.utils.timezone import now
def parse_int(value, default=0):
    try:
        return int(value) if value is not None and value.strip() != '' else default
    except (ValueError, TypeError):
        return default


def update_event_option(request, event_option):
    # Définition des options avec leurs méthodes de prix de base et clés POST
    options = [
        {"name": "MurFloral", "prix_base_method": event_option.prix_base_MurFloral, "prix_brut": "MurFloral_reduc_prix"},
        {"name": "Phonebooth", "prix_base_method": event_option.prix_base_Phonebooth, "prix_brut": "Phonebooth_reduc_prix"},
        {"name": "LivreOr", "prix_base_method": event_option.prix_base_LivreOr, "prix_brut": "LivreOr_reduc_prix"},
        {"name": "Fond360", "prix_base_method": event_option.prix_base_Fond360,"prix_brut": "Fond360_reduc_prix"},
        {"name": "PanneauBienvenue", "prix_base_method": event_option.prix_base_PanneauBienvenue,"prix_brut": "PanneauBienvenue_reduc_prix"},
        {"name": "Holo3D", "prix_base_method": event_option.prix_base_Holo3D, "prix_brut": "Holo3D_reduc_prix"},
        {"name": "PhotographeVoguebooth", "prix_base_method": event_option.prix_base_PhotographeVoguebooth, "prix_brut": "PhotographeVoguebooth_reduc_prix"},
        {"name": "ImpressionVoguebooth", "prix_base_method": event_option.prix_base_ImpressionVoguebooth, "prix_brut": "ImpressionVoguebooth_reduc_prix"},
        {"name": "DecorVoguebooth", "prix_base_method": event_option.prix_base_DecorVoguebooth, "prix_brut": "DecorVoguebooth_reduc_prix"},

        # Magnets retiré de cette liste
        # Ajoutez d'autres options ici si nécessaire
    ]

    total_option = 0
    for option in options:
        option_active = request.POST.get(option["name"]) == 'on'
        reduc_prix = parse_int(request.POST.get(option["prix_brut"], 0))

        if option_active:
            setattr(event_option, option["name"], option_active)
            setattr(event_option, f"{option['name']}_reduc_prix", reduc_prix)

            prix_base = option["prix_base_method"]()
            total_option += prix_base - reduc_prix

    # Traitement spécifique pour les magnets après la boucle des autres options
    event_option.magnets = parse_int(request.POST.get('magnets', 0))
    event_option.magnets_reduc_prix = parse_int(request.POST.get('magnets_reduc_prix'))
    if event_option.magnets:
        # Assurez-vous que la méthode prix_base_magnets est bien définie pour accepter un paramètre dans votre modèle.
        total_option += event_option.prix_base_magnets(event_option.magnets) - event_option.magnets_reduc_prix

    event_option.save()
    return total_option


def update_data(event, request):

    client = event.client
    event_details = event.event_details
    event_product = event.event_product
    event_option = event.event_option

    # Mise à jour des informations du page_client
    client.raison_sociale = request.POST.get('raison_sociale') == 'on'

    client.nom = request.POST.get('client_nom')
    client.mail = request.POST.get('client_mail')
    client.numero_telephone = request.POST.get('client_numero_telephone')
    client.how_find = request.POST.get('client_how_find')
    client.save()

    # Mise à jour des détails de l'événement
    event_details.date_evenement = request.POST.get('date_evenement')
    event_details.adresse_evenement = request.POST.get('adresse_evenement')
    event_details.ville_evenement = request.POST.get('ville_evenement')
    event_details.code_postal_evenement = request.POST.get('code_postal_evenement')
    event_details.comment = request.POST.get('comment')
    event_details.comment_client = request.POST.get('comment_client')
    event_details.horaire = request.POST.get('horaire')
    event_details.save()

    if event.prix_valided:
        event_template = event.event_template or EventTemplate(statut=False)
        event_template.url_modele = request.POST.get('url_modele')
        event_template.text_template = request.POST.get('text_template')
        event_template.link_media_shared = request.POST.get('link_media_shared')
        event_template.save()

        if not event.event_template:
            event.event_template = event_template
            event.save()

        else:
            new_directory_name = normalize_name(event)
            if new_directory_name != event.event_template.directory_name:
                rennaming_pcloud_event_folder(event, new_directory_name, prepa=True)
                rennaming_pcloud_event_folder(event, new_directory_name)
                event.event_template.directory_name = new_directory_name
                event.event_template.save()
                event.save()

    # Mise à jour des produits de l'événement
    event_product.photobooth = request.POST.get('photobooth') == 'on'
    event_product.miroirbooth = request.POST.get('miroirbooth') == 'on'
    event_product.videobooth = request.POST.get('videobooth') == 'on'
    event_product.voguebooth = request.POST.get('voguebooth') == 'on'
    event_product.ipadbooth = request.POST.get('ipadbooth') == 'on'
    event_product.airbooth = request.POST.get('airbooth') == 'on'
    event_product.save()

    # Mise à jour des options de l'événement et calcul du total
    total_option = update_event_option(request, event_option)

    # LIVRAISON
    event_option.MurFloral = request.POST.get('MurFloral') == 'on'
    if event_option.MurFloral :
        event_option.mur_floral_style = request.POST.get('mur_floral_style')
    event_option.Phonebooth = request.POST.get('Phonebooth') == 'on'
    event_option.LivreOr = request.POST.get('LivreOr') == 'on'
    event_option.Fond360 = request.POST.get('Fond360') == 'on'
    event_option.PanneauBienvenue = request.POST.get('PanneauBienvenue') == 'on'
    event_option.Holo3D = request.POST.get('Holo3D') == 'on'
    event_option.PhotographeVoguebooth = request.POST.get('PhotographeVoguebooth') == 'on'
    event_option.ImpressionVoguebooth = request.POST.get('ImpressionVoguebooth') == 'on'
    event_option.DecorVoguebooth = request.POST.get('DecorVoguebooth') == 'on'
    event_option.magnets = request.POST.get('magnets', '0')
    event_option.livraison = request.POST.get('livraison') == 'on'
    event_option.duree = request.POST.get('duree', '0')
    event_option.save()

    event.prix_brut = parse_int(request.POST.get('prix_brut'))
    event.reduc_product = parse_int(request.POST.get('reduc_product', '0'))
    event.reduc_all = parse_int(request.POST.get('reduc_all', '0'))

    int_prix_livraison, str_prix_livraison = calcul_prix_distance(event)

    event.prix_proposed = parse_int(request.POST.get('prix_proposed'))
    event.prix_proposed = event.prix_brut - event.reduc_product - event.reduc_all + total_option + int_prix_livraison

    if event.status == 'Initied':
        event.status = 'Calculed'
    event.save()

    return event


def process_event_update_bdd(event, form):
    """
    Process the event by creating or updating associated EventAcompte and EventTemplate,
    and updating the event details.

    Args:
        event: The event object to process.
        form: The form containing the cleaned data for acompte and other event details.

    Returns:
        bool: True if the transaction is successful, False otherwise.
    """
    try:
        with transaction.atomic():  # Garantit une transaction atomique

            # 1. Calculer le montant d'acompte
            montant_acompte = (
                form.data.get('autre_montant')
                if form.data.get('montant_acompte') == 'autre_montant'
                else form.data.get('montant_acompte')
            )

            montant_acompte = int(montant_acompte)

            # 2. Mise à jour ou création de l'acompte
            acompte, created_acompte = EventAcompte.objects.update_or_create(
                event=event,
                defaults={
                    'montant_acompte': montant_acompte,
                    'mode_payement': form.data.get('mode_payement', ''),  # Valeur par défaut vide
                    'date_payement': form.data.get('date_payement', None),  # Valeur par défaut None
                    'montant_restant': event.prix_proposed - montant_acompte,
                }
            )

            # 3. Mise à jour ou création du template de l'événement
            event_template, created_template = EventTemplate.objects.update_or_create(
                pk=event.event_template.pk if event.event_template else None,
                defaults={
                    'directory_name': normalize_name(event),
                }
            )

            # 4. Mise à jour des détails de l'événement
            event.event_template = event_template
            event.prix_valided = event.prix_proposed
            event.event_acompte = acompte
            event.signer_at = now()
            event.status = 'Acompte OK'
            event.save()  # Sauvegarde les changements

        # Retour succès
        return True

    except Exception as e:
        return False


def process_validation_event(event, form):
    """
    Process the event validation steps and track the failing step if any.

    Args:
        event: The event object to process.
        form: The submitted form with cleaned data.

    Returns:
        tuple: (all_success, failing_step)
            - all_success (bool): True if all steps succeed, False otherwise.
            - failing_step (str): The name of the first failing step, or None if all succeed.
    """

    # Initialiser l'acompte à None pour l'utiliser entre les étapes
    steps = [
        ("MAJ Event BDD", lambda: process_event_update_bdd(event, form)),
        ("Envoyer mail confirmation", lambda: send_mail_event(event, 'validation')),
        ("Deplacement Carte Trello", lambda: to_acompte_ok(event)),
        ("Génération du code espace client", lambda: generate_code_espace_client(event)),
        ("Création du dossier PREPA", lambda: create_pcloud_event_folder(event, prepa=True)),
        ("Création du dossier CLIENT", lambda: create_pcloud_event_folder(event)),
        ("Création du dossier MONTAGE", lambda: create_pcloud_event_folder(event, montage=True)),
    ]

    # Retirer conditionnellement certaines étapes si signer_at est défini
    if event.signer_at:
        steps = [
            step for step in steps
            if step[0] not in {
                "Envoyer mail confirmation",
            }
        ]

    for step_name, step_function in steps:
        if not step_function():
            return False, step_name  # Retourne le statut global et l'étape échouée

    return True, None  # Si toutes les étapes réussissent

