from django.shortcuts import redirect, get_object_or_404
from datetime import datetime, timedelta
from django.http import QueryDict
from .models import Event
from threading import Thread
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from .module.data_bdd.import_devis import upload_all_data
from .module.data_bdd.post_form import initialize_event, get_confirmation_data
from .module.data_bdd.update_event import update_data
from .module.devis_pdf.generate_pdf import generate_devis_pdf
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .module.devis_pdf.mail import send_email
from .module.trello.create_card import create_card
from .module.trello.move_card import to_acompte_ok, to_list_devis_fait

today_date = datetime.now().date()

def import_data_devis(request):
    upload_all_data()
    all_event = Event.objects.all().order_by('-created_at')
    return render(request, 'app/lst_devis.html', {'all_event': all_event,})

def demande_devis(request):
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form_data = request.POST.dict()
        request.session['demande_devis_data'] = form_data
        print(form_data)
        return render(request, 'app/confirmation.html', {'form_data': form_data})

    # Vérifiez d'abord s'il y a des données préremplies dans la session
    form_data = request.session.get('demande_devis_data', {})

    # Créez un objet QueryDict à partir des données pour préremplir le formulaire
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)

    return render(request, 'app/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'form': initial_data  # Utilisez initial_data pour préremplir le formulaire
    })


def confirmation(request):

    if request.method == 'POST':

        post_data = get_confirmation_data(request)

        initialize_event(post_data)

        create_card(post_data)

        return redirect('remerciement')  # Redirigez vers une URL de succès après la sauvegarde

    return render(request, 'app/confirmation.html')


def remerciement(request):
    return render(request, 'app/remerciement.html')


def lst_devis(request):
    all_event = Event.objects.all().order_by('-created_at')
    for event in all_event:
        print(event.client.nom)
    return render(request, 'app/lst_devis.html', {'all_event': all_event,})


def info_event(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'app/info_event.html', {'event': event})


@require_http_methods(["POST"])
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    update_data(event, request)

    # Rediriger vers la page de détails de l'événement mise à jour
    return redirect('info_event', id=event.id)


@require_http_methods(["POST"])
def validation_devis(request, id):
    event = get_object_or_404(Event, id=id)

    # MAJ BDD
    event.signer_at = today_date
    event.status = 'Acompte OK'
    event.prix_valided = event.prix_proposed
    event.save()

    # MAJ TRELLO
    to_acompte_ok(event)

    # Rediriger vers la page de détails de l'événement mise à jour
    return redirect('info_event', id=event.id)


# Vue qui affiche la page de confirmation
def confirmation_del_devis(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/confirmation_del_devis.html', {'event': event})


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


def generate_pdf(request, event_id):
    # Récupérez les données de l'événement en fonction de l'event_id
    event = Event.objects.get(id=event_id)

    buffer = generate_devis_pdf(event)

    # Réinitialisez le tampon et renvoyez le PDF en tant que réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facture.pdf"'
    return response


# Vue qui affiche la page de confirmation
def confirmation_envoi_mail(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/confirmation_envoi_mail.html', {'event': event})


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

            return render(request, 'app/retour_lst_devis.html', {'mail': True})
        else:
            return render(request, 'app/retour_lst_devis.html', {'mail': False}, status=500)
    else:
        # Redirigez vers la page de confirmation si la méthode n'est pas POST
        return redirect('confirmation_envoi_mail', event_id=event_id)


def preparation_presta(request):
    return render(request, 'preparation_presta/PRESTA-S06-2024.html')