from django.shortcuts import render, redirect, get_object_or_404
from ..models import Event, EventPostPrestation
from app.module.mail.send_mail_event import send_mail_event
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods

from ..module.cloud.create_timelaps import get_pcloud_print_folder, create_timelaps
from ..module.cloud.get_pcloud_data import get_pcloud_event_folder_data, \
    find_pcloud_empty_folder
from ..module.cloud.send_media import check_media_to_send
from ..module.cloud.share_link import get_pcloud_link_event_folder
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

    folder_to_send = check_media_to_send(event)
    folder_data = get_pcloud_event_folder_data(event.event_template.directory_name)

    if "Prints" in folder_to_send:
        # TODO if il y a dossier Client Event Prints and if not timelaps exist
        print_folder_data = get_pcloud_print_folder(folder_data)
        create_timelaps(event, folder_data, print_folder_data)
        event.event_template.link_media_shared = get_pcloud_link_event_folder(folder_data)
        event.event_template.save()
        send_mail_event(event, 'send_media')

    find_pcloud_empty_folder(folder_data)
    event.event_post_presta.sent = True
    event.event_post_presta.save()

    return redirect('post_presta')