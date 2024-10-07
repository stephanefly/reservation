from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from ..models import Event
from ..module.espace_client.logging import process_client_request
from ..module.espace_client.send_mail_espace_client import send_mail_espace_client
from ..module.espace_client.completer import update_event_and_redirect
from datetime import datetime, timedelta, timezone

today_date = datetime.now().date()

def logging_client(request):
    context = {'form': {}}
    if request.method == 'POST':
        form_data = request.POST.dict()
        client_mail = form_data.get('mail')
        date_str = form_data.get('date_evenement')
        today_date = datetime.now().date()
        event, result = process_client_request(client_mail, date_str, today_date)
        if event:
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
    return redirect('tableau_de_bord')


