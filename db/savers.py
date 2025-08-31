import pandas as pd

def save_to_csv(data: list[dict], path: str):
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print(f"Data saved to {path}")

# todo  DB ORM methods
# check python version in terminal: python --version