import os
from babel.dates import parse_date
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from datetime import datetime, timedelta, timezone
from django.http import QueryDict
from django.template.loader import render_to_string
import uuid
from .forms import CostForm, ValidationForm, CommentaireForm, HoraireForm
from .models import Event, Cost, EventAcompte, Client, EventDetails, EventTemplate
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .module.data_bdd.price import PRIX_PRODUITS
from .module.data_bdd.make_planning import make_planning, get_member_list
from .module.data_bdd.post_form import initialize_event, get_confirmation_data
from .module.data_bdd.update_event import update_data
from .module.devis_pdf.generate_pdf import generate_pdf_devis, generate_pdf_facture
from django.http import HttpResponse
from .module.devis_pdf.mail import send_email
from .module.espace_client.choose_to_relance import choose_to_relance
from .module.espace_client.completer import update_event_and_redirect
from .module.espace_client.logging import process_client_request
from .module.espace_client.send_mail_espace_client import send_mail_espace_client
from .module.lib_graph.lib_graph_all import tracage_figure_bar_bokeh, table_graph
from .module.lib_graph.lib_pie_chart import table_graph_pie
from .module.lib_graph.mise_en_week import new_mise_en_week, mise_en_week_avoir
from .module.trello.create_card import create_card
from .module.trello.get_trello_data import get_prio_card_name, get_all_card, get_data_card_by_name
from .module.trello.move_card import to_acompte_ok, to_list_devis_fait, to_refused
from .module.lib_graph.get_data import get_ok_data, get_cost_data
from .module.trello.update_data_card import update_option_labels_trello

today_date = datetime.now().date()

# FRONTEND
def demande_devis(request):
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form_data = request.POST.dict()
        request.session['demande_devis_data'] = form_data
        print("pré-confirmation " + str(form_data))
        return render(request, 'app/frontend/confirmation.html', {'form_data': form_data})

    # Vérifiez d'abord s'il y a des données préremplies dans la session
    form_data = request.session.get('demande_devis_data', {})

    # Créez un objet QueryDict à partir des données pour préremplir le formulaire
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)

    return render(request, 'app/frontend/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'form': initial_data  # Utilisez initial_data pour préremplir le formulaire
    })


def confirmation(request):

    if request.method == 'POST':

        post_data = get_confirmation_data(request)

        event = initialize_event(post_data)

        id_card = create_card(post_data)

        event.id_card = id_card
        event.save()

        return redirect('remerciement')  # Redirigez vers une URL de succès après la sauvegarde

    return render(request, 'app/frontend/confirmation.html')


def remerciement(request):
    return render(request, 'app/frontend/remerciement.html')

# -------------------------------------------------------

def lst_devis(request):
    all_event = Event.objects.all().order_by('-created_at')
    return render(request, 'app/backend/lst_devis.html', {'all_event': all_event, })


def lst_cost(request):
    all_cost = Cost.objects.all().order_by('-created_at')
    return render(request, 'app/backend/lst_cost.html', {'all_cost': all_cost, })


def info_event(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'app/backend/info_event.html', {'event': event})


@require_http_methods(["POST"])
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    update_data(event, request)
    update_option_labels_trello(event)

    # Rediriger vers la page de détails de l'événement mise à jour
    return redirect('info_event', id=event.id)


def confirmation_val_devis(request, id):
    event = Event.objects.get(pk=id)
    if request.method == 'POST':
        form = ValidationForm(request.POST)
        if form.is_valid():
            if event.status != "Acompte OK":
                send_mail_espace_client(event, 'validation')

            event_acompte = EventAcompte(
                montant_acompte=form.cleaned_data.get('montant_acompte'),
                mode_payement=form.cleaned_data.get('mode_payement'),
                date_payement=form.cleaned_data.get('date_payement'),
            )
            event_acompte.save()
            event.prix_valided = event.prix_proposed
            event.event_acompte = event_acompte  # Associe le nouvel objet EventAcompte à l'événement
            event_acompte.montant_restant = event.prix_proposed - int(event_acompte.montant_acompte)
            event_acompte.save()
            event.signer_at = today_date
            event.status = 'Acompte OK'

            event.save()  # Sauvegarde l'objet Event avec toutes les mises à jou

            # MAJ TRELLO
            to_acompte_ok(event)

            return redirect('lst_devis')  # Remplacez par l'URL de votre choix
    else:
        form = ValidationForm()
    return render(request, 'app/backend/confirmation_val_devis.html', {'form': form, 'event' : event})


@require_http_methods(["POST"])
def refused_devis(request, id):
    event = get_object_or_404(Event, id=id)
    # MAJ BDD
    event.status = 'Refused'
    event.save()

    # MAJ TRELLO
    to_refused(event)

    # Rediriger vers la page de détails de l'événement mise à jour
    return redirect('info_event', id=event.id)


# Vue qui affiche la page de confirmation
def confirmation_del_devis(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/backend/confirmation_del_devis.html', {'event': event})


@require_http_methods(["POST"])
def del_devis(request, id):
    event = get_object_or_404(Event, id=id)
    if event.client:
        event.client.delete()
    if event.event_details:
        event.event_details.delete()
    if event.event_option:
        event.event_option.delete()
    if event.event_product:
        event.event_product.delete()
    # Maintenant, supprimez l'événement lui-même
    event.delete()

    return redirect('lst_devis')


def generate_devis_pdf(request, event_id):
    # Récupérez les données de l'événement en fonction de l'event_id
    event = Event.objects.get(id=event_id)

    buffer = generate_pdf_devis(event)

    # Réinitialisez le tampon et renvoyez le PDF en tant que réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="devis.pdf"'
    return response

def generate_facture_pdf(request, event_id):
    # Récupérez les données de l'événement en fonction de l'event_id
    event = Event.objects.get(id=event_id)

    buffer = generate_pdf_facture(event)

    # Réinitialisez le tampon et renvoyez le PDF en tant que réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facture.pdf"'
    return response

# Vue qui affiche la page de confirmation
def confirmation_envoi_mail(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/backend/confirmation_envoi_mail.html', {'event': event})


# Vue modifiée pour l'envoi de l'email
def envoi_mail_devis(request, event_id):
    if request.method == 'POST':  # Assurez-vous que la confirmation a été faite
        event = Event.objects.get(id=event_id)
        if send_email(event):

            # MAJ BDD
            event.status = 'Sended'
            event.save()

            # MAJ TRELLO
            to_list_devis_fait(event)

            return render(request, 'app/backend/retour_lst_devis.html', {'mail': True})
        else:
            return render(request, 'app/backend/retour_lst_devis.html', {'mail': False}, status=500)
    else:
        # Redirigez vers la page de confirmation si la méthode n'est pas POST
        return redirect('confirmation_envoi_mail', event_id=event_id)


def graph(request):
    df_all_week = new_mise_en_week(get_ok_data())
    script, div = tracage_figure_bar_bokeh(df_all_week, today_date.strftime('%Y-%m-%d'))
    return render(request, 'app/backend/graph_all.html', {'script': script, 'div': div})


def graph_cost(request):
    df_all_week = new_mise_en_week(get_ok_data())
    df_brut_net = mise_en_week_avoir(df_all_week, get_cost_data())
    date_now = today_date.strftime('%Y-%m-%d')
    script, div = table_graph(df_brut_net, date_now)
    return render(request, 'app/backend/graph_cost.html', {'script': script, 'div': div})


def graph_cost_pie(request):
    script, div = table_graph_pie(get_ok_data(), get_cost_data())
    return render(request, 'app/backend/graph_cost_pie.html', {'script': script, 'div': div})


def create_cost(request):
    if request.method == 'POST':
        form = CostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lst_cost')  # Remplacez par l'URL de votre choix
    else:
        form = CostForm()
    return render(request, 'app/backend/create_cost.html', {'form': form})


def info_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    form = CostForm(instance=cost)
    return render(request, 'app/backend/info_cost.html',
                  {'cost': cost, 'form': form, 'id':id})


@require_http_methods(["POST"])
def edit_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    form = CostForm(request.POST, instance=cost)
    if form.is_valid():
        form.save()
        return redirect('lst_cost')


@require_http_methods(["POST"])
def delete_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    cost.delete()
    return redirect('lst_cost')


def tableau_de_bord(request):

    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=10)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_event_prio)
    print(event_lst_member)

    return render(request, 'app/backend/tableau_de_bord.html',
                  {
                      'lst_event_prio': lst_event_prio,
                      'event_lst_member': event_lst_member
                  })


# TACHE PLANIFIEES
def tache_planif():
    maj_today_event()
    make_planning()


def logging_client(request):
    context = {'form': {}}

    if request.method == 'POST':
        form_data = request.POST.dict()
        client_mail = form_data.get('mail')
        date_str = form_data.get('date_evenement')
        today_date = datetime.now().date()

        # Appeler la fonction utilitaire
        event, result = process_client_request(client_mail, date_str, today_date)

        if event:
            # Stocker le token en session ou dans la base de données
            request.session['client_token'] = result
            return redirect('choix_client', id=event.id, token=result)
        else:
            context['error_message'] = result

    return render(request, 'app/page_client/logging.html', context)


def choix_client(request, id, token):
    if 'client_token' in request.session and request.session['client_token'] == token:
        event = Event.objects.get(pk=id)
        return render(request, 'app/page_client/info_client_event.html', {'event': event})
    else:
        return render(request, 'app/page_client/logging.html')


@require_http_methods(["POST"])
def edit_horaire(request, event_id):
    return update_event_and_redirect(request, event_id, 'horaire', 'event_details', 'choix_client')

@require_http_methods(["POST"])
def edit_comment(request, event_id):
    return update_event_and_redirect(request, event_id, 'comment_client', 'event_details', 'choix_client')

@require_http_methods(["POST"])
def edit_text(request, event_id):
    return update_event_and_redirect(request, event_id, 'text_template', 'event_template', 'choix_client')

@require_http_methods(["POST"])
def edit_template(request, event_id):
    return update_event_and_redirect(request, event_id, 'url_modele', 'event_template', 'choix_client')

def relance_espace_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_espace_client(event, 'relance')
    return redirect('lst_cost')


def tarifs(request):
    return render(request, 'app/frontend/tarifs.html', {'data_price': PRIX_PRODUITS})