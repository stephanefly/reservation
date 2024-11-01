from django.shortcuts import render, redirect, get_object_or_404
from ..forms import ValidationForm
from ..models import Event, EventAcompte
from ..module.data_bdd.update_event import update_data
from app.module.mail.send_mail_event import send_mail_event
from ..module.ftp_myselfiebooth.connect_ftp import SFTP_STORAGE
from ..module.trello.update_data_card import update_option_labels_trello
from ..module.trello.move_card import to_acompte_ok, to_refused, to_list_devis_fait
from ..module.devis_pdf.generate_pdf import generate_pdf_devis, generate_pdf_facture
from django.views.decorators.http import require_http_methods
from datetime import datetime
from django.http import HttpResponse

today_date = datetime.now().date()


def lst_devis(request):
    all_event = Event.objects.all().order_by('-created_at')
    return render(request, 'app/backend/lst_devis.html', {'all_event': all_event})


def info_event(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'app/backend/info_event.html', {'event': event})


@require_http_methods(["POST"])
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    update_data(event, request)
    # update_option_labels_trello(event)
    return redirect('info_event', id=event.id)


# Vue qui affiche la page de confirmation
def confirmation_del_devis(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'app/backend/confirmation_del_devis.html', {'event': event})


def confirmation_val_devis(request, id):
    event = Event.objects.get(pk=id)
    if request.method == 'POST':
        form = ValidationForm(request.POST)
        if form.is_valid():
            if event.signer_at is None:
                send_mail_event(event, 'validation')
                to_acompte_ok(event)

            event_acompte = EventAcompte(
                montant_acompte=form.cleaned_data.get('montant_acompte'),
                mode_payement=form.cleaned_data.get('mode_payement'),
                date_payement=form.cleaned_data.get('date_payement'),
            )
            event_acompte.save()
            event.prix_valided = event.prix_proposed
            event.event_acompte = event_acompte
            event_acompte.montant_restant = event.prix_proposed - int(event_acompte.montant_acompte)
            event_acompte.save()
            event.signer_at = today_date
            event.status = 'Acompte OK'
            event.save()

            SFTP_STORAGE._create_event_repository(event)
            return redirect('info_event', id=event.id)
    else:
        form = ValidationForm()
    return render(request, 'app/backend/confirmation_val_devis.html', {'form': form, 'event': event})


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

def desabonner(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.client.autorisation_mail = False
    event.client.save()  # Enregistrer l'objet client
    return render(request, 'app/frontend/desabonnement.html')
