import pandas as pd
from db.connection import get_engine

df = pd.read_csv("data/all_inventory.csv", sep=";", encoding="latin1")

def save_inventory_to_db(df, table_name):
    engine = get_engine()
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"✅ Saved {len(df)} rows to table '{table_name}' in PostgreSQL.")

save_inventory_to_db(df, "products")