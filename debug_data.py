import pandas as pd
from data_loader import load_data

print("Loading data...")
df_pres, df_herb, df_path = load_data()

print("\n--- Prescription ---")
print("Columns:", df_pres.columns.tolist())
print(df_pres.head(2))

print("\n--- Herb Library ---")
print("Columns:", df_herb.columns.tolist())
print(df_herb.head(2))

print("\n--- Pathology ---")
print("Columns:", df_path.columns.tolist())
print(df_path.head(2))
