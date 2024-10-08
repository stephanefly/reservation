
from ..module.data_bdd.make_planning import get_member_list
from django.shortcuts import render, redirect, get_object_or_404
from ..models import Event, EventPostPrestation
from ..module.espace_client.send_mail_espace_client import send_mail_espace_client
from datetime import datetime, timedelta, timezone

def relance_avis_client(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    send_mail_espace_client(event, 'relance_avis')
    return redirect('tableau_de_bord')

def presta_fini(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    event.status = "Presta FINI"
    event.save()
    return redirect('post_presta')


def update_post_presta_status(request, post_presta_id, action):
    post_presta = get_object_or_404(EventPostPrestation, pk=post_presta_id)

    if action == 'paid':
        post_presta.paid = True
    elif action == 'membre_paid':
        post_presta.membre_paid = True
    elif action == 'feedback':
        post_presta.feedback = True
    elif action == 'feedback_posted':
        post_presta.feedback_posted = True
    elif action == 'sent':
        post_presta.sent = True
    else:
        return redirect('error_page')  # Gestion d'erreur si l'action est inconnue

    post_presta.save()
    return redirect('post_presta')


def post_presta(request):
    today_date = datetime.now()

    lst_post_event = Event.objects.filter(
        signer_at__isnull=False,
        status='Post Presta'
    ).order_by('event_details__date_evenement')

    # event_lst_member = get_member_list(lst_post_event)

    return render(request, 'app/backend/post_presta.html',
                  {
                      'lst_post_event': lst_post_event,
                  })
