from datetime import datetime
import json
import pandas as pd
import os
from app.models import NameCost, Cost


def upload_avoir():
    # Ouvrir le fichier JSON et charger les données
    with open(r'app/module/import_data/avoirs.json', 'r', encoding='utf-8') as file:
        data_avoir = json.load(file)

    # Convertir les données JSON en DataFrame Pandas
    df = pd.DataFrame(data_avoir)


    # names_uniques = df['Client'].unique()
    # for page_client in names_uniques:
    #     NameCost.objects.create(name=page_client)

    for i in df.iloc:
        # Conversion de Timestamp en str
        date_obj = datetime.strptime(i['Date'], '%d/%m/%Y')

        cost_int = Cost.objects.create(
            name_cost=NameCost.objects.get(name=i['Client']),
            type_cost=i['Type'],
            price_cost=i['Montant HT'],
        )

        Cost.objects.filter(pk=cost_int.id).update(created_at=date_obj)
