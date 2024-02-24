from datetime import datetime

import pandas as pd

from app.models import NameCost, Cost


def upload_avoir():
    df = pd.read_json(r'app\module\import_data\avoirs.json')

    names_uniques = df['Client'].unique()
    for client in names_uniques:
        NameCost.objects.create(name=client)

    for i in df.iloc:
        # Conversion de Timestamp en str
        date_str = i['Date'].strftime('%d/%m/%Y')

        # Utilisation de strptime() pour convertir la chaîne de caractères en datetime
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')

        cost_int = Cost.objects.create(
            name_cost=NameCost.objects.get(name=i['Client']),
            type_cost=i['Type'],
            price_cost=i['Montant HT'],
        )

        Cost.objects.filter(pk=cost_int.id).update(created_at=date_obj)
