from app.module.cloud.get_pcloud_data import create_pcloud_event_folder
from app.module.devis_pdf.make_table import calcul_prix_distance
from app.module.espace_client.data_client import generate_code_espace_client
from app.module.cloud.rennaming import normalize_name
from app.module.external_sync import queue_pcloud_rename
from app.module.data_bdd.event_pricing import parse_int, update_event_option
from app.models import EventTemplate, EventAcompte
from app.module.mail.send_mail_event import send_mail_event
from app.module.trello.move_card import to_acompte_ok
from django.db import transaction
from django.utils.timezone import now
from app.module.notion.notion_service import create_notion_card

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
        if event_product.videobooth and event.prix_valided:
            event_template.url_music_360 = request.POST.get('url_music_360')
        event_template.save()

        if event.event_post_presta:
            event.event_post_presta.link_media_shared = request.POST.get('link_media_shared') or None
            event.event_post_presta.save(update_fields=['link_media_shared'])

        if not event.event_template:
            event.event_template = event_template
            event.save()

        else:
            new_directory_name = normalize_name(event)
            if new_directory_name != event.event_template.directory_name:
                queue_pcloud_rename(event.event_template.directory_name, new_directory_name)
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

    # Mise à jour de la tarification
    event.prix_brut = parse_int(request.POST.get('prix_brut'))
    event.reduc_product = parse_int(request.POST.get('reduc_product', '0'))
    event.reduc_all = parse_int(request.POST.get('reduc_all', '0'))

    int_prix_livraison, str_prix_livraison = calcul_prix_distance(event)

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
    Retourne :
        all_success : bool
        failing_steps : liste de tuples (step_name, error_message)
    """

    steps = [
        ("MAJ Event BDD",                     lambda: process_event_update_bdd(event, form)),
        ("Envoyer mail confirmation",         lambda: send_mail_event(event, 'validation')),
        ("Deplacement Carte Trello",          lambda: to_acompte_ok(event)),
        ("Création Calendrier Notion",        lambda: create_notion_card(event)),
        ("Génération du code espace client",  lambda: generate_code_espace_client(event)),
        ("Création du dossier PREPA",         lambda: create_pcloud_event_folder(event, prepa=True)),
        ("Création du dossier CLIENT",        lambda: create_pcloud_event_folder(event)),
        ("Création du dossier MONTAGE",       lambda: create_pcloud_event_folder(event, montage=True)),
    ]

    if event.signer_at:
        steps = [
            (name, fn) for name, fn in steps
            if name not in {"Envoyer mail confirmation"}
        ]

    failing = []

    for step_name, fn in steps:
        try:
            result = fn()
            if not result:
                failing.append((step_name, "La fonction a renvoyé False ou None"))
        except Exception as e:
            failing.append((step_name, str(e)))

    all_success = len(failing) == 0

    return all_success, failing

