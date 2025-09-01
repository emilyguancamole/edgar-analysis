import psycopg
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    return psycopg.connect(
        dbname="edgar_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

