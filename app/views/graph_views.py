from django.shortcuts import render
from ..module.lib_graph.lib_graph_all import tracage_figure_bar_bokeh, table_graph
from ..module.lib_graph.lib_pie_chart import table_graph_pie
from ..module.lib_graph.mise_en_week import new_mise_en_week, mise_en_week_avoir
from ..module.lib_graph.get_data import get_ok_data, get_cost_data
from datetime import datetime, timedelta, timezone

today_date = datetime.now().date()

def graph(request):
    df_all_week = new_mise_en_week(get_ok_data())
    script, div = tracage_figure_bar_bokeh(df_all_week, today_date.strftime('%Y-%m-%d'))
    return render(request, 'app/backend/graph_all.html', {'script': script, 'div': div})

def graph_cost(request):
    df_all_week = new_mise_en_week(get_ok_data())
    df_brut_net = mise_en_week_avoir(df_all_week, get_cost_data())
    date_now = today_date.strftime('%Y-%m-%d')
    script, div = table_graph(df_brut_net, date_now)
    return render(request, 'app/backend/graph_cost.html', {'script': script, 'div': div})

def graph_cost_pie(request):
    script, div = table_graph_pie(get_ok_data(), get_cost_data())
    return render(request, 'app/backend/graph_cost_pie.html', {'script': script, 'div': div})
