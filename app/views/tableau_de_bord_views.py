from django.shortcuts import render, redirect, get_object_or_404
from ..models import Event, TeamMember
from ..module.data_bdd.make_planning import get_member_list
from datetime import datetime, timedelta, timezone
import json
from django.http import HttpResponse
from django.template.loader import render_to_string

def tableau_de_bord(request):
    today_date = datetime.now()
    today_minus_6h = today_date - timedelta(hours=6)
    end_week_date = today_date + timedelta(days=30)
    team_members = TeamMember.objects.all()

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_minus_6h, end_week_date]
    ).order_by('event_details__date_evenement')


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
    return HttpResponse(render_to_string('partials/members.html', {'event': event}))

def api_remove_member(request, event_id, member_id):
    event = Event.objects.get(id=event_id)
    member = TeamMember.objects.get(id=member_id)
    event.event_team_members.remove(member)
    return HttpResponse(render_to_string('partials/members.html', {'event': event}))