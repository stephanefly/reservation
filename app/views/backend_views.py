from django.shortcuts import render, redirect, get_object_or_404
from ..forms import ValidationForm
from ..models import Event, EventAcompte, EventTemplate

from ..module.data_bdd.update_event import update_data, process_validation_event
from app.module.mail.send_mail_event import send_mail_event

from ..module.trello.update_data_card import update_option_labels_trello, update_trello_date
from ..module.trello.move_card import to_acompte_ok, to_refused, to_list_devis_fait
from ..module.devis_pdf.generate_pdf import generate_pdf_devis, generate_pdf_facture
from django.views.decorators.http import require_http_methods
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q

today_date = datetime.now().date()

def lst_devis(request):
    # Récupération des paramètres de filtre
    nom = request.GET.get('nom', '').strip()
    tel = request.GET.get('tel', '').strip()
    date_event = request.GET.get('date_event', '').strip()
    prix_min = request.GET.get('prix_min', '').strip()
    prix_max = request.GET.get('prix_max', '').strip()
    status = request.GET.get('status', '').strip()

    # Initialisation de la requête avec les 15 derniers événements
    all_event = Event.objects.all().order_by('-created_at')[:15]

    # Appliquer les filtres dynamiquement
    filters = Q()  # Initialisez une requête vide

    if nom:
        filters &= Q(client__nom__icontains=nom)
    if tel:
        filters &= Q(client__numero_telephone__icontains=tel)
    if date_event:
        filters &= Q(event_details__date_evenement__icontains=date_event)
    if prix_min.isdigit():
        filters &= Q(prix_proposed__gte=int(prix_min))
    if prix_max.isdigit():
        filters &= Q(prix_proposed__lte=int(prix_max))
    if status:
        filters &= Q(status=status)  # Filtre exact sur le statut

    # Appliquer les filtres si spécifiés
    if filters:
        all_event = Event.objects.filter(filters).order_by('-created_at')

    # Renvoyer les résultats au template
    return render(request, 'app/backend/lst_devis.html', {
        'all_event': all_event,
        'filters': {
            'nom': nom,
            'tel': tel,
            'date_event': date_event,
            'prix_min': prix_min,
            'prix_max': prix_max,
            'status': status,
        },
        'status_choices': Event.STATUS,  # Passer les choix de status au template
    })


def info_event(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'app/backend/info_event.html', {'event': event})


@require_http_methods(["POST"])
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    update_data(event, request)
    update_trello_date(event)
    update_option_labels_trello(event)
    return redirect('info_event', id=event.id)


# Vue qui affiche la page de confirmation
def confirmation_del_devis(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/backend/confirmation_del_devis.html', {'event': event})


def confirmation_val_devis(request, id):
    event = get_object_or_404(Event, pk=id)
    form = ValidationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():

        all_success, failing_step = process_validation_event(event, form)

        return render(request, 'app/backend/validation_process_event.html', {
            'failing_step': failing_step,
            'all_success': all_success,
            'event': event,
        }
                      )

    return render(request, 'app/backend/confirmation_val_devis.html', {
        'form': form,
        'event': event
    })


def refused_devis(request, id):
    event = get_object_or_404(Event, id=id)
    event.status = 'Refused'
    event.save()
    to_refused(event)
    return redirect('info_event', id=event.id)


def del_devis(request, id):
    event = get_object_or_404(Event, id=id)
    event.delete()
    return redirect('lst_devis')


def generate_devis_pdf(request, event_id):
    event = Event.objects.get(id=event_id)
    buffer = generate_pdf_devis(event)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="devis.pdf"'
    return response


def generate_facture_pdf(request, event_id):
    event = Event.objects.get(id=event_id)
    buffer = generate_pdf_facture(event)
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
        if send_mail_event(event,'devis'):

            # MAJ BDD
            if event.signer_at is None:
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


def relance_devis_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_event(event, 'relance_devis')
    return redirect('info_event', id=event.id)


def action_once(request):
    return redirect('lst_devis')
