from django.shortcuts import render
from ..models import Event
from ..module.data_bdd.make_planning import get_member_list
from datetime import datetime, timedelta, timezone

def tableau_de_bord(request):
    today_date = datetime.now()
    today_minus_6h = today_date - timedelta(hours=6)
    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_minus_6h, end_week_date]
    ).order_by('event_details__date_evenement')

    event_lst_member = get_member_list(lst_event_prio)

    return render(request, 'app/backend/tableau_de_bord.html',
                  {
                      'lst_event_prio': lst_event_prio,
                      'event_lst_member': event_lst_member
                  })
