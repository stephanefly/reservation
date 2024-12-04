import pandas as pd
from django.db.models import Q
from app.models import Event, Cost


def get_ok_data():
    pd.set_option('display.max_columns', None)
    results = Event.objects.filter(
        Q(status__icontains="Presta FINI")
        |Q(status__icontains="Acompte OK")
        |Q(status__icontains="Post Presta")
    ).filter(signer_at__isnull=False
    ).select_related(
        'client_id',  # Suppose un ForeignKey vers AppClient
        'event_product_id',  # Suppose un ForeignKey vers AppEventProduct
        'event_details_id'  # Suppose un ForeignKey vers AppEventDetails
    ).values(
        'client_id__nom',  # Accéder au champ `nom` de la relation page_client
        'prix_proposed',
        'event_details_id__date_evenement',  # Accéder à date_evenement à travers la relation
        'event_product_id__photobooth',  # Accéder à photobooth à travers la relation
        'event_product_id__miroirbooth',  # Accéder à miroirbooth à travers la relation
        'event_product_id__videobooth',  # Accéder à videobooth à travers la relation
        'event_product_id__voguebooth',  # Accéder à photobooth à travers la relation
        'event_product_id__ipadbooth',  # Accéder à miroirbooth à travers la relation
        'event_product_id__airbooth',  # Accéder à videobooth à travers la relation
    )

    df = pd.DataFrame(results)
    df['event_product_id__photobooth'] = df['event_product_id__photobooth'].astype(int)
    df['event_product_id__miroirbooth'] = df['event_product_id__miroirbooth'].astype(int)
    df['event_product_id__videobooth'] = df['event_product_id__videobooth'].astype(int)
    df['event_product_id__voguebooth'] = df['event_product_id__voguebooth'].astype(int)
    df['event_product_id__ipadbooth'] = df['event_product_id__ipadbooth'].astype(int)
    df['event_product_id__airbooth'] = df['event_product_id__airbooth'].astype(int)

    df = df.rename(columns={
        'client_id__nom': 'Names',
        'prix_proposed': 'Prix',
        'event_details_id__date_evenement': 'Date-Event',
        'event_product_id__photobooth': 'Photobooth',
        'event_product_id__miroirbooth': 'Miroirbooth',
        'event_product_id__videobooth' : '360Booth',
        'event_product_id__voguebooth': 'Voguebooth',
        'event_product_id__ipadbooth': 'Ipadbooth',
        'event_product_id__airbooth': 'Airbooth',
    })

    return df

def get_cost_data():

    # Configuration pour afficher toutes les colonnes dans les DataFrames
    pd.set_option('display.max_columns', None)

    # Récupération des données depuis la base de données
    # Les champs récupérés incluent : type de coût, prix, date de création, et fréquence.
    results = Cost.objects.all().values(
        'type_cost',
        'price_cost',
        'created_at',
        'frecency',  # Fréquence
    )

    # Conversion des données récupérées en DataFrame pour un traitement plus facile
    df = pd.DataFrame(results)
    df = df.rename(columns={
        'type_cost': 'Type',       # Renommage pour une meilleure lisibilité
        'price_cost': 'Cost',      # Nom simplifié pour le coût
        'created_at': 'Date-Event',  # Date associée à l'événement
        'frecency': 'Frequency',   # Fréquence de coût (Mensuel, Annuel, etc.)
    })

    # Gestion des coûts annuels
    # Objectif : diviser les coûts annuels par 12 pour générer des coûts mensuels
    annual_costs = df[df['Frequency'] == 'Annuel'].copy()
    annual_to_monthly_costs = []

    for _, row in annual_costs.iterrows():
        if row['Cost'] is not None and row['Date-Event'] is not None:
            cost_per_month = row['Cost'] / 12  # Division du coût annuel par 12
            start_date = pd.to_datetime(row['Date-Event'])  # Conversion de la date en format datetime

            # Générer 12 coûts mensuels (chaque début de mois)
            for i in range(12):
                month_date = start_date + pd.DateOffset(months=i)  # Ajout de mois successifs
                annual_to_monthly_costs.append({
                    'Type': row['Type'],                      # Type de coût (ex : Charge, Invest)
                    'Cost': cost_per_month,                   # Coût mensuel
                    'Date-Event': month_date.replace(day=1),  # Fixer la date au 1er de chaque mois
                    'Frequency': 'Mensuel (from Annuel)',     # Indication de l'origine
                })

    # Gestion des coûts mensuels
    # Objectif : répliquer les coûts mensuels chaque 1er du mois pendant 12 mois
    monthly_costs = df[df['Frequency'] == 'Mensuel'].copy()
    recurring_monthly_costs = []

    for _, row in monthly_costs.iterrows():
        if row['Cost'] is not None and row['Date-Event'] is not None:
            start_date = pd.to_datetime(row['Date-Event'])  # Conversion de la date en format datetime

            # Générer 12 occurrences du coût mensuel
            for i in range(12):
                month_date = start_date + pd.DateOffset(months=i)  # Ajout de mois successifs
                recurring_monthly_costs.append({
                    'Type': row['Type'],                      # Type de coût (ex : Charge, Invest)
                    'Cost': row['Cost'],                      # Montant du coût mensuel
                    'Date-Event': month_date.replace(day=1),  # Fixer la date au 1er de chaque mois
                    'Frequency': 'Mensuel (Recurrent)',       # Indication de l'origine
                })

    # Supprimer les lignes d'origine pour les coûts annuels et mensuels
    # On les remplace par les coûts générés
    df = df[~df['Frequency'].isin(['Annuel', 'Mensuel'])]

    # Combiner le DataFrame initial (sans Annuel/Mensuel) avec les nouveaux coûts générés
    df = pd.concat([
        df,
        pd.DataFrame(annual_to_monthly_costs),    # Ajout des coûts mensuels générés à partir des annuels
        pd.DataFrame(recurring_monthly_costs),   # Ajout des récurrences mensuelles
    ], ignore_index=True)

    # Trier le DataFrame par date pour une meilleure organisation
    df = df.sort_values(by='Date-Event').reset_index(drop=True)

    # Retourner le DataFrame final
    return df
