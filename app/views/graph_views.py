from django.shortcuts import render
from ..module.lib_graph.lib_graph_all import tracage_figure_bar_bokeh, table_graph, tracage_figure_bar_cost, \
    tracage_figure_bar_potentiel
from ..module.lib_graph.lib_pie_chart import table_graph_pie
from ..module.lib_graph.mise_en_week import new_mise_en_week, mise_en_week_avoir
from ..module.lib_graph.get_data import get_ok_data, get_cost_data
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
    # Même jeu de données signé pour les trois comparaisons annuelles.
    # On ne filtre pas sur la date de signature : 2027 inclut les réservations déjà signées.
    script, div = tracage_figure_bar_potentiel(get_ok_data(), date_now)
    return render(request, 'app/backend/graph/graph_potentiel.html', {'script': script, 'div': div})

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