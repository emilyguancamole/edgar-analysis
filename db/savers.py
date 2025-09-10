import os
import pandas as pd

def save_to_csv(data: list[dict], path: str):
    """ Add new rows to CSV, avoiding duplicates based on accession_number """
    df_new = pd.DataFrame(data)
    if os.path.exists(path):
        df_existing = pd.read_csv(path, dtype=str)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset=['accession_number'], inplace=True)
        df_combined.to_csv(path, index=False)
        print(f"Saved records to {path}.")
    else:
        df_new.to_csv(path, index=False)
        print(f"Saved records to NEW file {path}.")

# todo  DB ORM methods
# check python version in terminal: python --version