
import logging
import secrets

from django.http import HttpResponseBadRequest, QueryDict
from app.module.data_bdd.panneau_xxl import TARIFS_PANNEAUX, QUANTITE_PAR_DEFAUT, quantite_panneaux
from django.shortcuts import render, redirect, get_object_or_404
from datetime import timedelta, datetime

from ..models import Event
from ..module.data_bdd.post_form import initialize_event, get_confirmation_data
from ..module.data_bdd.instant_quote import preparer_et_envoyer_devis
from app.module.mail.send_mail_event import send_mail_event
from django.conf import settings
from ..module.data_bdd.price import PRIX_PRODUITS
from ..module.google.contact import create_google_contact
from ..module.trello.create_card import create_card

logger = logging.getLogger(__name__)

today_date = datetime.now().date()

def demande_devis(request):
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
        except ValueError as error:
            return HttpResponseBadRequest(str(error))
        request.session['demande_devis_data'] = form_data
        return render(request, 'app/frontend/confirmation.html', {'form_data': form_data})

    form_data = request.session.get('demande_devis_data', {})
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)

    return render(request, 'app/frontend/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'quantites_panneaux': TARIFS_PANNEAUX.items(),
        'panneaux_choisis': int(form_data.get('panneaux_xxl') or 0) or QUANTITE_PAR_DEFAUT,
        'form': initial_data
    })

def confirmation(request):
    if request.method == 'POST':
        try:
            panneaux = quantite_panneaux(request.POST)
        except ValueError as error:
            return HttpResponseBadRequest(str(error))
        post_data = get_confirmation_data(request)
        post_data['panneaux_xxl'] = panneaux

        # Initialise l'event AVANT redirect
        event = initialize_event(post_data)
        event.event_token = secrets.token_hex(32)
        event.save()

        # Création Google Contact
        try:
            create_google_contact(event)
        except:
            pass

        # Trello est optionnel : une panne ne doit pas bloquer la demande enregistrée.
        try:
            event.id_card = create_card(post_data)
            event.save(update_fields=['id_card'])
        except Exception:
            logger.exception("Création Trello échouée pour l'événement %s", event.id)

        # Option désactivée par défaut : aucun devis n'est envoyé sans validation
        # préalable des tarifs et de la délivrabilité. RECOMMANDATION reste manuelle.
        if getattr(settings, "INSTANT_QUOTES_ENABLED", False):
            try:
                preparer_et_envoyer_devis(event, send_mail_event)
            except Exception:
                # Ne jamais perdre la demande en cas de problème de prix ou de SMTP.
                # L'événement reste dans le CRM pour traitement manuel.
                logger.exception(
                    "Devis instantané non traité pour l'événement %s (manuel requis)",
                    event.id,
                )

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
    return render(request, 'app/frontend/tarifs.html', {'data_price': PRIX_PRODUITS, 'tarifs_panneaux': TARIFS_PANNEAUX.items()})

def brochure(request):
    return render(request, 'app/frontend/brochure.html', {'tarifs_panneaux': TARIFS_PANNEAUX.items()})