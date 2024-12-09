from django.shortcuts import render
from ..module.lib_graph.lib_graph_all import tracage_figure_bar_bokeh, table_graph, tracage_figure_bar_cost, \
    tracage_figure_bar_potentiel
from ..module.lib_graph.lib_pie_chart import table_graph_pie
from ..module.lib_graph.mise_en_week import new_mise_en_week, mise_en_week_avoir
from ..module.lib_graph.get_data import get_ok_data, get_cost_data, get_ok_data_before
from datetime import datetime, timedelta, timezone

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

    df_all_week_before = new_mise_en_week(get_ok_data_before(days_delta=365))
    df_brut_net_before = mise_en_week_avoir(df_all_week_before, get_cost_data())

    df_all_week_now = new_mise_en_week(get_ok_data())
    df_brut_net_now = mise_en_week_avoir(df_all_week_now, get_cost_data())

    script, div = tracage_figure_bar_potentiel(df_brut_net_now, df_brut_net_before, date_now)
    return render(request, 'app/backend/graph/graph_potentiel.html', {'script': script, 'div': div})