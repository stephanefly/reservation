
import logging
import secrets
from datetime import date
from types import SimpleNamespace
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from django.http import HttpResponseBadRequest, QueryDict
from app.module.data_bdd.panneau_xxl import TARIFS_PANNEAUX, QUANTITE_PAR_DEFAUT, quantite_panneaux
from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta, datetime

from ..models import Event
from ..module.data_bdd.post_form import initialize_event, get_confirmation_data
from quote_control.service import process_instant_quote
from quote_control.public_pricing import get_public_catalogue
from app.module.mail.send_mail_event import send_mail_event

from ..module.google.contact import create_google_contact
from ..module.trello.create_card import create_card

logger = logging.getLogger(__name__)

FORM_PENDING = 'Formulaire : confirmation non terminée'


def _validate_quote_fields(post):
    """Contrôle serveur : la première étape est désormais enregistrée en base."""
    required = ('mail', 'numero_telephone', 'date_evenement', 'ville_evenement',
                'code_postal_evenement', 'adresse_evenement', 'selectedImages')
    if any(not str(post.get(field) or '').strip() for field in required):
        raise ValueError('Veuillez compléter tous les champs obligatoires.')
    if not (post.get('raison_sociale') or (post.get('nom') and post.get('prenom'))):
        raise ValueError('Veuillez renseigner votre nom ou votre société.')
    try:
        validate_email(post['mail'])
        date_event = date.fromisoformat(post['date_evenement'])
        duration = int(post.get('heure_range') or 0)
        quantities = [int(post.get(field) or 0) for field in
                      ('magnets_range', 'PorteCles_range', 'MagnetsSimple_range')]
    except (ValidationError, ValueError, TypeError):
        raise ValueError('Adresse e-mail, date ou quantité invalide.') from None
    if date_event < timezone.localdate() or date_event > timezone.localdate() + timedelta(days=730):
        raise ValueError("La date de l'événement est hors de la période autorisée.")
    if duration not in range(3, 8) or any(q < 0 or q > 10000 for q in quantities):
        raise ValueError('Durée ou quantité invalide.')
    if not (str(post.get('numero_telephone') or '').isdigit() and
            len(post['numero_telephone']) == 10 and post['numero_telephone'].startswith('0')):
        raise ValueError('Numéro de téléphone invalide.')
    if not (str(post.get('code_postal_evenement') or '').isdigit() and len(post['code_postal_evenement']) == 5):
        raise ValueError('Code postal invalide.')
    allowed = {'Photobooth', 'Miroirbooth', '360Booth', 'Voguebooth', 'Ipadbooth', '360Airbooth'}
    products = set(post['selectedImages'].split(','))
    if not products or not products <= allowed:
        raise ValueError('Sélectionnez une prestation valide.')


def demande_devis(request):
    today_date = timezone.localdate()
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form_data = request.POST.dict()
        try:
            quantite = quantite_panneaux(request.POST)
            form_data["avec_panneaux"] = "on" if quantite else ""
            form_data["panneaux_xxl"] = str(quantite)
            form_data["panneaux_forfait"] = TARIFS_PANNEAUX.get(quantite, 0)
            _validate_quote_fields(form_data)
            data = get_confirmation_data(SimpleNamespace(POST=form_data))
            data['panneaux_xxl'] = quantite
            previous_id = request.session.get('draft_event_id')
            draft = Event.objects.filter(pk=previous_id, status='Initied',
                                         history_status=FORM_PENDING, event_token__isnull=True).first() if previous_id else None
            event = initialize_event(data, existing=draft)
            event.history_status = FORM_PENDING
            event.save(update_fields=['history_status'])
            request.session['draft_event_id'] = event.id
            request.session.pop('quote_confirmed_event_id', None)
        except (ValueError, TypeError, KeyError, ValidationError) as error:
            logger.warning('Première étape devis refusée : données invalides.')
            return HttpResponseBadRequest(str(error))
        request.session['demande_devis_data'] = form_data
        return render(request, 'app/frontend/confirmation.html', {'form_data': form_data})

    form_data = request.session.get('demande_devis_data', {})
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)
    initial_data['today_date'] = today_date_str
    initial_data['date_dans_deux_ans'] = date_dans_deux_ans_str

    return render(request, 'app/frontend/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'quantites_panneaux': TARIFS_PANNEAUX.items(),
        'panneaux_choisis': int(form_data.get('panneaux_xxl') or 0) or QUANTITE_PAR_DEFAUT,
        'form': initial_data
    })

def confirmation(request):
    if request.method == 'POST':
        if request.session.get('quote_confirmed_event_id'):
            return redirect('remerciement')

        form_data = request.session.get('demande_devis_data')
        if not form_data:
            return HttpResponseBadRequest('Session expirée : veuillez recommencer le formulaire.')
        try:
            _validate_quote_fields(form_data)
            panneaux = quantite_panneaux(form_data)
            post_data = get_confirmation_data(SimpleNamespace(POST=form_data))
            post_data['panneaux_xxl'] = panneaux
        except (ValueError, TypeError, KeyError, ValidationError):
            return HttpResponseBadRequest('Demande invalide : veuillez reprendre le formulaire.')

        draft_id = request.session.get('draft_event_id')
        if draft_id:
            event = Event.objects.filter(pk=draft_id, status='Initied',
                                         history_status=FORM_PENDING,
                                         event_token__isnull=True).first()
            if event is None:
                return HttpResponseBadRequest('Cette demande a déjà été traitée ou a expiré.')
        else:
            # Compatibilité avec les sessions créées avant la mise à jour du site.
            event = initialize_event(post_data)
        event.event_token = secrets.token_hex(32)
        event.history_status = 'Formulaire : demande confirmée'
        event.save(update_fields=['event_token', 'history_status'])

        try:
            create_google_contact(event)
        except Exception:
            logger.exception("Contact Google non créé pour dossier %s", event.id)

        try:
            event.id_card = create_card(post_data)
            event.save(update_fields=['id_card'])
        except Exception:
            logger.exception("Création Trello échouée pour l'événement %s", event.id)

        process_instant_quote(event, send_mail_event)
        request.session.pop('draft_event_id', None)
        request.session.pop('demande_devis_data', None)
        request.session['quote_confirmed_event_id'] = event.id
        return redirect('remerciement')

    return render(request, 'app/frontend/confirmation.html')


def desabonner(request, token):
    event = Event.objects.get(event_token=token)
    event.client.autorisation_mail = False
    if event.status not in ['Refused', 'Presta FINI']:
        event.status = 'Mail_Refused'
        event.save()
    event.client.save()  # Enregistrer l'objet client
    return render(request, 'app/frontend/desabonnement.html')

def remerciement(request):
    return render(request, 'app/frontend/remerciement.html')

def tarifs(request):
    context = get_public_catalogue()
    context["tarifs_panneaux"] = TARIFS_PANNEAUX.items()
    return render(request, 'app/frontend/tarifs.html', context)

def brochure(request):
    context = get_public_catalogue()
    context["tarifs_panneaux"] = TARIFS_PANNEAUX.items()
    return render(request, 'app/frontend/brochure.html', context)