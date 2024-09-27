from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, HoverTool, DatetimeTickFormatter, Range1d
from bokeh.layouts import column, grid
import pandas as pd
import datetime
from bokeh.embed import components

def tracage_figure_bar_bokeh(df_all_prix, date_now):

    df_all_prix["date2"] = df_all_prix['Date-Event']+pd.offsets.DateOffset(years=1, days=-1)
    df_all_prix["date3"] = df_all_prix['Date-Event']+pd.offsets.DateOffset(years=1, days=-1.75)

    df_all_prix['Date1'] = df_all_prix['Date-Event'] - pd.Timedelta(days=6)
    df_all_prix['Date2'] = df_all_prix['Date-Event']

    source = ColumnDataSource(data=df_all_prix)

    hover = HoverTool(tooltips=[
        ("week", "@Date1{%d/%m/%Y} - @Date2{%d/%m/%Y}"),
        ("Photobooth", "@PrixPhotobooth € (@Photobooth)"),
        ("Miroirbooth", "@PrixMiroirbooth € (@Miroirbooth)"),
        ("360Booth", "@Prix360Booth € (@360Booth)"),
        ("Voguebooth", "@PrixVoguebooth € (@Voguebooth)"),
        ("Ipadbooth", "@PrixIpadbooth € (@Ipadbooth)"),
        ("Airbooth", "@PrixAirbooth € (@Airbooth)"),
        ("Total-week", "@Prix €")],
        formatters={'@Date1': 'datetime', '@Date2': 'datetime'})

    # ... rest of the code ...

    produit = ["PrixPhotobooth", "PrixMiroirbooth", "Prix360Booth", "PrixVoguebooth", "PrixIpadbooth", "PrixAirbooth"]
    colors = ["#87CEEB", "#FFD700", "#BA55D3", "#50d150", "#000000", "#f6a2f3"]

    # GRAPHE 2021
    graph2021 = figure(title="2021", width=1150, height=300,tools=[hover])
    graph2021.vbar_stack(produit, x='Date-Event', fill_color=colors,legend_label=produit,
                         source=source, width=datetime.timedelta(weeks=1))
    graph2021.legend.background_fill_alpha = 0.2
    graph2021.x_range = Range1d(pd.to_datetime("2021-01-01"), pd.to_datetime("2021-12-30"))
    graph2021.y_range = Range1d(0, 3300)
    graph2021.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                 months=["%d %b %Y"],
                                                 years=["%d %b %Y"]
                                                      )
    # GRAPHE 2022
    graph2022 = figure(title="2022", width=1150, height=300,tools=[hover])
    graph2022.vbar_stack(produit, x='Date-Event', fill_color=colors,legend_label=produit,
                         source=source, width=datetime.timedelta(weeks=1))
    graph2021.legend.background_fill_alpha = 0.2
    graph2022.vbar(pd.to_datetime(date_now), top=3000, width=1.5, color="red")
    graph2022.x_range = Range1d(pd.to_datetime("2022-01-01"), pd.to_datetime("2022-12-30"))
    graph2022.y_range = Range1d(0, 3300)
    graph2022.legend.location = "top_left"
    graph2022.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                 months=["%d %b %Y"],
                                                 years=["%d %b %Y"]
                                                 )
    # GRAPHE 2023
    graph2023 = figure(title="2023", width=1150, height=300,tools=[hover])
    graph2023.vbar(x='date2', top ='Prix', fill_alpha=0, width=datetime.timedelta(weeks=1), source=source)
    graph2023.vbar_stack(produit, x='Date-Event', fill_color=colors, legend_label=produit,
                         source=source, width=datetime.timedelta(weeks=1))
    graph2023.legend.background_fill_alpha = 0.2
    graph2023.vbar(pd.to_datetime(date_now), top=3000, width=1.5, color="red")
    graph2023.x_range = Range1d(pd.to_datetime("2023-01-01"), pd.to_datetime("2023-12-30"))

    graph2023.y_range = Range1d(0, 3300)
    graph2023.legend.location = "top_left"
    graph2023.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                 months=["%d %b %Y"],
                                                 years=["%d %b %Y"]
                                                 )
    # GRAPHE 2024
    graph2024 = figure(title="2024", width=1150, height=300,tools=[hover])
    graph2024.vbar(x='date3', top ='Prix', fill_alpha=0, width=datetime.timedelta(weeks=1), source=source)
    graph2024.vbar_stack(produit, x='Date-Event', fill_color=colors, legend_label=produit,
                         source=source, width=datetime.timedelta(weeks=1))
    graph2024.legend.background_fill_alpha = 0.2
    graph2024.vbar(pd.to_datetime(date_now), top=3000, width=1.5, color="red")
    graph2024.x_range = Range1d(pd.to_datetime("2024-01-01"), pd.to_datetime("2024-12-30"))

    graph2024.y_range = Range1d(0, 3300)
    graph2024.legend.location = "top_left"
    graph2024.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                 months=["%d %b %Y"],
                                                 years=["%d %b %Y"]
                                                      )

    # GRAPHE 2025
    graph2025 = figure(title="2025", width=1150, height=300,tools=[hover])
    graph2025.vbar(x='date4', top ='Prix', fill_alpha=0, width=datetime.timedelta(weeks=1), source=source)
    graph2025.vbar_stack(produit, x='Date-Event', fill_color=colors, legend_label=produit,
                         source=source, width=datetime.timedelta(weeks=1))
    graph2025.legend.background_fill_alpha = 0.2
    graph2025.vbar(pd.to_datetime(date_now), top=3000, width=1.5, color="red")
    graph2025.x_range = Range1d(pd.to_datetime("2025-01-01"), pd.to_datetime("2025-12-30"))

    graph2025.y_range = Range1d(0, 3300)
    graph2025.legend.location = "top_left"
    graph2025.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                 months=["%d %b %Y"],
                                                 years=["%d %b %Y"]
                                                      )
    layout = column(graph2025, graph2024, graph2023, graph2022, graph2021)

    return components(layout)


def tracage_figure_bar_cost(df_brut_net, year, date_now):

    df_brut_net['Date'] = df_brut_net['Date-Event'] - pd.Timedelta(days=6)

    source = ColumnDataSource(data=df_brut_net)

    hover = HoverTool(tooltips=[
        ("week", "@Date{%d %b %Y}"),
        ("Brut", "@Prix €"),
        ("Total Cost", "@Cost €"),
        ("Membre", "@Membre €"),
        ("Invest", "@Invest €"),
        ("Charge", "@Charge €"),
        ("Delegation", "@Delegation €"),
        ("Net", "@BeneficeNet €")],
        formatters={'@Date': 'datetime'})

    produit = ["BeneficeNet", "Membre", "Invest", "Charge", "Delegation"]
    colors = ['green', "blue", "violet", "red", "orange"]

    graph = figure(title=f"Resultat {year}",width=1150, height=300, tools=[hover])
    graph.vbar_stack(produit, x='Date-Event', fill_color=colors, color="black",
                     source=source, width=datetime.timedelta(weeks=1))
    graph.vbar(pd.to_datetime(date_now), top=3000, width=1.5, color="red")
    graph.x_range = Range1d(pd.to_datetime(f"{year}-01-01"), pd.to_datetime(f"{year}-12-30"))
    graph.y_range = Range1d(-1000, 4500)
    # graph.legend.location = "top_left"
    # graph.legend.background_fill_alpha = 0.2
    graph.xaxis.formatter = DatetimeTickFormatter(days=["%d %b %Y"],
                                                  months=["%d %b %Y"],
                                                  years=["%d %b %Y"])

    return components(graph)


def table_graph(df_brut_net, date_now):

    lst_year = [2025, 2024, 2023, 2022]
    script = []
    div = []
    for year in lst_year:
        components = tracage_figure_bar_cost(df_brut_net, year, date_now)
        script.append(components[0])
        div.append(components[1])

    return script, div

