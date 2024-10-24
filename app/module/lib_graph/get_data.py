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

    pd.set_option('display.max_columns', None)
    results = Cost.objects.all().values(
        'type_cost',
        'price_cost',
        'created_at',
    )
    df = pd.DataFrame(results)
    df = df.rename(columns={
        'type_cost': 'Type',
        'price_cost': 'Cost',
        'created_at': 'Date-Event',
    })
    return df
