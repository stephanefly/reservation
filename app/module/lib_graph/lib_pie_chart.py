from math import pi
import pandas as pd
from bokeh.io import show
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource
from bokeh.embed import components



def tracer_figure_pie_chart(df_all_ok, df_all_cost, year):
    # Conversion des dates
    df_all_ok["Date-Event"] = pd.to_datetime(df_all_ok["Date-Event"])
    df_all_cost["Date-Event"] = pd.to_datetime(df_all_cost["Date-Event"])

    # Filtrage par année
    df_ok = df_all_ok[df_all_ok["Date-Event"].dt.year == year]
    df_cost = df_all_cost[df_all_cost["Date-Event"].dt.year == year]

    # Calcul des totaux
    brut_total_year = df_ok["Prix"].sum()
    cost_total_year = df_cost["Cost"].sum()
    net_total_year = brut_total_year - cost_total_year
    rentable = round((net_total_year / cost_total_year) * 100, 0) if cost_total_year else 0

    # Préparation des données pour le diagramme
    data = {
        'sectors': ['Dépense', 'Bénéfice'],
        'end_angle': [cost_total_year / brut_total_year * 2 * pi,
                      (brut_total_year - cost_total_year) / brut_total_year * 2 * pi],
        'color': ['red', 'green'],
        'value': [cost_total_year, net_total_year],
        'percentage': [cost_total_year / brut_total_year, net_total_year / brut_total_year]
    }
    source = ColumnDataSource(data=data)

    # Création du diagramme
    p = figure(title=f"Résultats {year}", width=800, height=300,
               toolbar_location=None, tools='hover', tooltips='@sectors: @value{0.00} €',
               x_range=(-1, 1))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('end_angle', include_zero=True), end_angle=cumsum('end_angle'),
            line_color='white', fill_color='color', legend_field='sectors', source=source)

    # Masquer les axes et les grilles
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    # Afficher le diagramme
    show(p)

    # Renvoyer le script et le div pour l'intégration dans un site web
    return components(p)

def table_graph_pie(df_all_ok, df_all_cost):

    lst_year = [2024, 2023, 2022]
    script = []
    div = []
    for year in lst_year:
        components = tracer_figure_pie_chart(df_all_ok, df_all_cost, year)
        script.append(components[0])
        div.append(components[1])

    return script, div
