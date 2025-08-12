from django.shortcuts import render
from ..models import TeamMember, Event
from django.db.models import Count, Q, Prefetch



def comptabilite(request):
    # 1) Filtre commun des events + tri par date
    lst_post_event = (
        Event.objects
        .filter(
            signer_at__isnull=False,
            event_post_presta__sold_ok=False,
            status__in=['Post Presta', 'Sent Media']
        )
        .select_related('event_details')  # pour éviter les N+1 en accédant à la date
        .order_by('event_details__date_evenement')
    )

    # 2) Annoter chaque membre avec le nombre d'events filtrés + précharger ces events
    members = (
        TeamMember.objects
        .annotate(
            nb_prestations=Count('events', filter=Q(events__in=lst_post_event), distinct=True)
        )
        .prefetch_related(
            Prefetch('events', queryset=lst_post_event, to_attr='post_events')
        )
        .order_by('-nb_prestations', 'name')
    )

    # 3) Mapping voulu {Nom: [event_1, event_2, ...]}
    member_events = {m.name: list(m.post_events) for m in members if m.nb_prestations > 0}

    # 4) Contexte envoyé au template
    context = {
        'members': members,
        'member_events': member_events,
    }

    return render(request, 'app/backend/comptabilite.html', context)
