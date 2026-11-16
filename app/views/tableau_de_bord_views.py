from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from ..models import Event, TeamMember
from ..module.team.planning_schedule import get_team_planning_values
from datetime import datetime, timedelta, timezone
import json
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

def tableau_de_bord(request):
    today_date = datetime.now()
    today_minus_6h = today_date - timedelta(hours=6)
    end_week_date = today_date + timedelta(days=30)
    team_members = TeamMember.objects.all()

    lst_event_prio = Event.objects.select_related(
        'client', 'event_details', 'event_product', 'event_option',
        'event_acompte', 'event_template', 'event_post_presta',
    ).filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_minus_6h, end_week_date]
    ).order_by('event_details__date_evenement')


    for event in lst_event_prio:
        event.team_planned_start, event.team_planned_duration = get_team_planning_values(event)

    return render(request, 'app/backend/tableau_de_bord.html',
                  {
                      'lst_event_prio': lst_event_prio,
                      'team_members': team_members,
                  })

def api_add_member(request, event_id):

    data = json.loads(request.body)
    event = Event.objects.get(id=event_id)
    member = TeamMember.objects.get(id=data['member_id'])
    event.event_team_members.add(member)
    return HttpResponse(render_to_string('app/partials/members.html', {'event': event}))

def api_remove_member(request, event_id, member_id):
    event = Event.objects.get(id=event_id)
    member = TeamMember.objects.get(id=member_id)
    event.event_team_members.remove(member)
    return HttpResponse(render_to_string('app/partials/members.html', {'event': event}))

@require_POST
def update_comment(request, event_id):
    payload = json.loads(request.body.decode("utf-8"))
    value = payload.get("value", "").strip()
    event = get_object_or_404(Event, id=event_id)

    # Mise à jour du champ comment de la table event_details
    event.event_details.comment = value
    event.event_details.save(update_fields=["comment"])

    return JsonResponse({"success": True, "event_id": event_id, "comment": value})
