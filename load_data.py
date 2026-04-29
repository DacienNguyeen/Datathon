import pandas as pd
from pathlib import Path

DATA_PATH = Path("data")

def load_orders():
    df = pd.read_csv(DATA_PATH / "orders.csv")
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

def load_traffic():
    df = pd.read_csv(DATA_PATH / "web_traffic.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df