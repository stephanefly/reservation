
import pandas as pd
from dateutil.relativedelta import relativedelta

from app.module.lib_graph.get_data import get_ok_data


def new_mise_en_week(df_all):

    # Nettoyage initial et remplacement des valeurs vides par 0
    df_all['Ponderation'] = df_all[['Photobooth', 'Miroirbooth', '360Booth']].fillna(0).sum(axis=1).astype(int)

    # Calcul des prix proportionnels pour chaque produit
    lst_produit = ['Photobooth', 'Miroirbooth', '360Booth']
    for produit in lst_produit:
        prix_colonne = f'Prix{produit}'
        for i in range(1, 4):
            df_all.loc[df_all['Ponderation'] == i, prix_colonne] = df_all['Prix'] / i * df_all[produit]

    # Conversion de la date en format datetime et tri par date
    df_all['Date-Event'] = pd.to_datetime(df_all['Date-Event'], format='%Y-%m-%d')
    df_all = df_all.sort_values(by='Date-Event')

    # Groupement des données par semaine pour les différents calculs
    agg_funcs = {'Prix': 'sum', 'PrixPhotobooth': 'sum', 'PrixMiroirbooth': 'sum',
                 'Prix360Booth': 'sum', 'Photobooth': 'sum', 'Miroirbooth': 'sum', '360Booth': 'sum'}
    df_all_grouped = df_all.groupby(pd.Grouper(key='Date-Event', freq='W')).agg(agg_funcs).reset_index().sort_values('Date-Event')

    # Ajout de la date de la dernière semaine et du dernier mois
    last_date = df_all_grouped["Date-Event"].iloc[-1]
    new_row1 = pd.DataFrame({
        'Date-Event': [last_date + relativedelta(months=3)],
        'Prix': [0]
    })
    new_row2 = pd.DataFrame({
        'Date-Event': [last_date + relativedelta(weeks=1)],
        'Prix': [0]
    })
    df_all_grouped = pd.concat([df_all_grouped, new_row1], ignore_index=True)
    df_all_grouped = pd.concat([df_all_grouped, new_row2], ignore_index=True)

    return df_all_grouped

def mise_en_week_avoir(df_all_week, df_cost_all):
    # Groupement par semaine et type, puis calcul de la somme des coûts pour chaque groupe
    df_week_type_cost = df_cost_all.groupby([pd.Grouper(key='Date-Event', freq='W'), 'Type'])['Cost'].sum().unstack(
        fill_value=0).reset_index()
    # Calcul de la somme des coûts totaux par semaine
    df_week_cost_sum = df_cost_all.groupby([pd.Grouper(key='Date-Event', freq='W')])['Cost'].sum().reset_index()
    df_week_cost_all = pd.merge(df_week_cost_sum, df_week_type_cost, on='Date-Event').sort_values('Date-Event')
    df_week_cost_all['Date-Event'] = pd.to_datetime(df_week_cost_all['Date-Event'].dt.tz_localize(None), format='%Y-%m-%d')

    df_brut_net = df_all_week.join(df_week_cost_all.set_index('Date-Event'), on='Date-Event', how='outer').fillna(0)

    df_brut_net = df_brut_net[['Date-Event', 'Cost', 'Prix', 'Charge', 'Invest', 'Membre']]
    df_brut_net['BeneficeNet'] = df_brut_net['Prix']-df_brut_net['Cost']

    return df_brut_net

