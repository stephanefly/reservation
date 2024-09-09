from math import pi
import pandas as pd
from bokeh.io import show
from bokeh.layouts import row
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource, Range1d
from bokeh.embed import components
from bokeh.models import FactorRange, HoverTool
from bokeh.palettes import Category20

def tracer_figure_pie_chart_all(df_all_ok, df_all_cost, year):
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
        'percentage': [f"{rentable}%"] * 2,  # Répéter la valeur de rentabilité pour chaque secteur
        'brut_total_year': [brut_total_year] * 2,  # Répéter pour chaque secteur
        'net_total_year': [net_total_year] * 2,  # Répéter pour chaque secteur
        'cost_total_year': [cost_total_year] * 2,  # Répéter pour chaque secteur
    }
    source = ColumnDataSource(data=data)

    # Définir les nouveaux tooltips
    TOOLTIPS = [
        ("Total-Brut", "@brut_total_year{0.00} €"),
        ("Bénéfice", "@net_total_year{0.00} €"),
        ("Dépense", "@cost_total_year{0.00} €"),
        ("Rentabilité", "@percentage"),
    ]
    # Création du diagramme
    p = figure(title=f"Résultats {year}", width=380, height=200,
               toolbar_location=None, tools='hover', tooltips=TOOLTIPS,
               x_range=(-1, 1))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('end_angle', include_zero=True), end_angle=cumsum('end_angle'),
            line_color='white', fill_color='color', legend_field='sectors', source=source)

    # Masquer les axes et les grilles
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    # Renvoyer le script et le div pour l'intégration dans un site web
    return p

def tracer_figure_pie_chart_split(df_all_ok, df_all_cost, year):
    # Conversion des dates
    df_all_ok["Date-Event"] = pd.to_datetime(df_all_ok["Date-Event"])
    df_all_cost["Date-Event"] = pd.to_datetime(df_all_cost["Date-Event"])

    # Filtrage par année
    df_ok = df_all_ok[df_all_ok["Date-Event"].dt.year == year]
    df_cost = df_all_cost[df_all_cost["Date-Event"].dt.year == year]

    # Exemple de calculs des totaux (assurez-vous que ces lignes soient correctement intégrées dans votre contexte)
    brut_total_year = df_ok["Prix"].sum()
    cost_total_year = df_cost["Cost"].sum()
    net_total_year = brut_total_year - cost_total_year

    # Calculs individuels des types de coûts
    membre = df_cost[df_cost['Type'] == "Membre"]['Cost'].sum()
    invest = df_cost[df_cost['Type'] == "Invest"]['Cost'].sum()
    charge = df_cost[df_cost['Type'] == "Charge"]['Cost'].sum()
    delegation = df_cost[df_cost['Type'] == "Delegation"]['Cost'].sum()

    # Préparation des données pour le diagramme
    total = net_total_year + membre + invest + charge + delegation
    values = [ charge,  invest,membre, net_total_year, delegation,]
    sectors=['Charge', 'Invest','Membre',  'Bénéfice', 'Delegation']
    color = [ 'red', 'violet','blue',  'green', 'orange']
    proportions = [value / total for value in values]
    angles = [prop * 2 * pi for prop in proportions]


    data = {
        'sectors': sectors,
        'start_angle': [sum(angles[:i]) for i in range(len(angles))],
        'end_angle': [sum(angles[:i + 1]) for i in range(len(angles))],
        'color': color,
        'value': values,
    }

    source = ColumnDataSource(data=data)

    # Création du diagramme
    p = figure(title="Répartition des coûts et bénéfice pour l'année", width=380, height=200, tools="hover",
               tooltips="@sectors: @value{0.00} €", x_range=(-1, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle='start_angle',
            end_angle='end_angle',
            line_color='white', fill_color='color', legend_field='sectors', source=source)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    # Renvoyer le script et le div pour l'intégration dans un site web
    return p

def tracer_figure_pie_chart_month(df_all_ok, df_all_cost, year):
    # Conversion des dates et regroupement par mois et type de coût
    df_all_ok['Date-Event'] = pd.to_datetime(df_all_ok['Date-Event'])
    df_all_cost['Date-Event'] = pd.to_datetime(df_all_cost['Date-Event'])

    # Regroupement par mois pour les revenus
    df_ok_monthly = df_all_ok[df_all_ok['Date-Event'].dt.year == year].groupby(df_all_ok['Date-Event'].dt.month).agg(
        {'Prix': 'sum'}).reset_index()

    # Regroupement par mois et type pour les dépenses
    df_cost_monthly = df_all_cost[df_all_cost['Date-Event'].dt.year == year].groupby(
        [df_all_cost['Date-Event'].dt.month, 'Type']).agg({'Cost': 'sum'}).reset_index()
    df_cost_monthly_pivot = df_cost_monthly.pivot(index='Date-Event', columns='Type', values='Cost').fillna(0)

    # Ajouter les mois à la source de données
    df_cost_monthly_pivot['months'] = [f"{month}-2024" for month in df_cost_monthly_pivot.index]

    # Obtenir la liste des noms de colonnes pour les types de coûts
    # Générer dynamiquement une liste de couleurs basée sur le nombre de stackers
    stackers = df_cost_monthly_pivot.columns[:-1].tolist()  # Tous les types de coûts sans la colonne 'months'
    if len(stackers) > 20:
        raise ValueError("Il y a plus de types de coûts que de couleurs disponibles dans la palette Category20.")
    colors = Category20[len(stackers)]

    # Création de la source de données pour le graphique
    source = ColumnDataSource(df_cost_monthly_pivot)
    source_ok = ColumnDataSource(df_ok_monthly)

    # Configuration des mois pour l'axe x
    months = [f"{month}-2024" for month in range(1, 13)]

    p = figure(x_range=FactorRange(*months), width=380, height=200,
               title=f"Répartition des coûts par Type pour chaque Mois {year}",
               toolbar_location=None, tools="")

    # Ajout du graphique à barres empilées
    p.vbar_stack(stackers, x='months', width=0.9, color=colors, source=source)

    # Configuration des propriétés visuelles
    p.y_range = Range1d(0, 4000)
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.xaxis.major_label_orientation = 1

    return p


def table_graph_pie(df_all_ok, df_all_cost):

    lst_year = [2024, 2023, 2022]
    script = []
    div = []
    for year in lst_year:
        p1 = tracer_figure_pie_chart_all(df_all_ok, df_all_cost, year)
        p2 = tracer_figure_pie_chart_split(df_all_ok, df_all_cost, year)
        p3 = tracer_figure_pie_chart_month(df_all_ok, df_all_cost, year)
        row_components = components(row(p1, p2, p3))
        script.append(row_components[0])
        div.append(row_components[1])

    return script, div
