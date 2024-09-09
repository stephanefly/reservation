from django.shortcuts import render
from ..models import EventTemplate, Event
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect, get_object_or_404

today_date = datetime.now().date()

def template_to_do(request):
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=10)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    return render(request, 'app/team/template_to_do.html', {
        'lst_event_prio': lst_event_prio,
    })

def change_status(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    event_template.statut = not event_template.statut
    event_template.save()
    return redirect('tableau_de_bord')
