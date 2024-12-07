from django.shortcuts import render, redirect, get_object_or_404
from ..models import Event, EventPostPrestation
from app.module.mail.send_mail_event import send_mail_event
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

from ..module.cloud.send_media import complete_and_check_media
from ..module.data_bdd.make_planning import get_member_list


def relance_avis_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_event(event, 'relance_avis')
    return redirect('tableau_de_bord')

def presta_fini(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.status = "Presta FINI"
    event.save()
    return redirect('post_presta')


@require_http_methods(["POST"])
def update_post_presta_status(request, post_presta_id, action):
    post_presta = get_object_or_404(EventPostPrestation, pk=post_presta_id)
    actions = {
        'paid': 'paid',
        'membre_paid': 'membre_paid',
        'feedback': 'feedback',
        'feedback_posted': 'feedback_posted',
        'sent': 'sent',
    }

    if action in actions:
        setattr(post_presta, actions[action], True)
        post_presta.save()
        return JsonResponse({'success': True, 'action': action, 'message': 'Statut mis à jour avec succès.'})
    else:
        return JsonResponse({'success': False, 'message': 'Action inconnue.'}, status=400)

    return HttpResponseBadRequest('Requête invalide.')


def post_presta(request):

    lst_post_event = Event.objects.filter(
        signer_at__isnull=False,
        status='Post Presta'
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_post_event)

    return render(request, 'app/backend/post_presta.html',
                  {
                      'lst_post_event': lst_post_event,
                      'event_lst_member': event_lst_member
                  })

def send_media(request, event_id):

    event = get_object_or_404(Event, pk=event_id)

    if complete_and_check_media(event):
        send_mail_event(event, 'send_media')
        event.event_post_presta.sent = True

    return redirect('post_presta')