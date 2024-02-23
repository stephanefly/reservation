import pandas as pd


def upload_avoir():
    df = pd.read_csv(r'app\module\import_data\avoirs.csv')
    print(df)