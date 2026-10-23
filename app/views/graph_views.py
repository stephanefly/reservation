from django.shortcuts import render
from ..module.lib_graph.lib_graph_all import tracage_figure_bar_bokeh, table_graph, tracage_figure_bar_cost
from ..module.lib_graph.lib_pie_chart import table_graph_pie
from ..module.lib_graph.mise_en_week import new_mise_en_week, mise_en_week_avoir
from ..module.lib_graph.get_data import get_ok_data, get_cost_data
from ..module.lib_graph.potentiel_statique import prepare_potentiel_charts
from datetime import datetime, timedelta, timezone
from ..models import Event


today_date = datetime.now().date()
date_now = today_date.strftime('%Y-%m-%d')

def graph(request):
    df_all_week = new_mise_en_week(get_ok_data())
    script, div = tracage_figure_bar_bokeh(df_all_week, date_now)
    return render(request, 'app/backend/graph/graph_all.html', {'script': script, 'div': div})


def graph_cost(request):
    df_all_week = new_mise_en_week(get_ok_data())
    df_brut_net = mise_en_week_avoir(df_all_week, get_cost_data())
    script, div = table_graph(df_brut_net, date_now)
    return render(request, 'app/backend/graph/graph_cost.html', {'script': script, 'div': div})


def graph_cost_pie(request):
    script, div = table_graph_pie(get_ok_data(), get_cost_data())
    return render(request, 'app/backend/graph/graph_cost_pie.html', {'script': script, 'div': div})


def graph_potentiel(request):
    # Les montants correspondent aux devis des prestations déjà signées.
    # Source directe SQL : aucun script Bokeh/JavaScript requis pour l'affichage.
    events = Event.objects.filter(
        signer_at__isnull=False,
        status__in=('Presta FINI', 'Acompte OK', 'Sent Media', 'Post Presta'),
        event_details__date_evenement__year__gte=2024,
        event_details__date_evenement__year__lte=2027,
    ).values_list('event_details__date_evenement', 'prix_proposed')

    charts = prepare_potentiel_charts(events)
    return render(
        request,
        'app/backend/graph/graph_potentiel.html',
        {'charts': charts},
    )


def cycle_strategique_view(request):
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=7)

    len_preparation = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).count()

    len_conversion = Event.objects.filter(status__in=["Sended", "Resended",'Last Chance', 'First Rappel', 'Last Rappel', 'Prolongation', 'Temoignage', 'Phonebooth Offert']).count()
    len_postprestation = Event.objects.filter(status__in=["Post Presta", 'Sent Media']).count()

    return render(request, 'app/backend/graph/cycle_strategique.html',
              {
                  'len_preparation': len_preparation,
                  'len_conversion': len_conversion,
                  'len_postprestation': len_postprestation,
              })