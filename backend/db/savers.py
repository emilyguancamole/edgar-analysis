import io
import os
import pandas as pd
from .connect_db import get_conn
from .load_data import merge_13f_staging_to_schema, merge_13g_staging_to_schema

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

def save_13f_to_db(data: list[dict], staging_table: str = "staging_13f"):
    """Load 13F CSV data into a staging table, and merge with 13F schema in postgres"""
    if not data:
        print("No 13F data to save")
        return
    conn = get_conn()
    df = pd.DataFrame(data)
    try:
        # Ensure funds are loaded before merging
        from .load_data import load_funds
        load_funds(conn)
        conn.commit()
        with conn.cursor() as cur:
        # _show_db_info(conn, cur)
            # Drop/create staging for each run
            cur.execute(f"DROP TABLE IF EXISTS {staging_table};")
            cur.execute(f"""
                CREATE TABLE {staging_table} (
                    accession_number TEXT,
                    report_date DATE,
                    cik TEXT,
                    issuer TEXT,
                    class TEXT,
                    cusip TEXT,
                    figi TEXT,
                    value_dollar NUMERIC,
                    shares_owned BIGINT,
                    share_type TEXT,
                    discretion TEXT,
                    voting_sole BIGINT,
                    voting_shared BIGINT,
                    voting_none BIGINT,
                    primary_doc_url TEXT
                )""")
            
            csv_io = io.StringIO() # creates in-memory text buffer (file-like obj) to r/w from like a file
            df.to_csv(csv_io, index=False)
            csv_io.seek(0)

        # COPY raw CSV into staging
        with conn.cursor() as cur:
            # COPY FROM copies data from a file to a table (appending)
            with cur.copy(f"COPY {staging_table} FROM STDIN WITH CSV HEADER") as copy:
                copy.write(csv_io.read())
        conn.commit()
        merge_13f_staging_to_schema(staging_table, conn)
        conn.commit()
        print(f"Saved {len(df)} 13F rows to DB {staging_table} and merged")

    except Exception as e:
        print("Error during COPY for 13F:", e)
        conn.rollback()
        raise
    finally:
        conn.close()

        
def save_13g_to_db(data: list[dict], staging_table: str = "staging_13g"):
    """Load 13G CSV data into a staging table, and merge with 13G schema in postgres"""
    if not data:
        print("No 13G data to save")
        return
    df = pd.DataFrame(data)
    conn = get_conn()
    try:
        # Ensure funds are loaded before merging
        from .load_data import load_funds
        load_funds(conn)
        conn.commit()
        with conn.cursor() as cur:
            # drop/create staging for each run
            cur.execute(f"DROP TABLE IF EXISTS {staging_table};")
            cur.execute(f"""
                CREATE TABLE {staging_table} (
                    accession_number TEXT,
                    cik TEXT,
                    primary_doc TEXT,
                    name_filer TEXT,
                    report_date DATE,
                    issuer TEXT,
                    cusip TEXT,
                    shares_owned BIGINT,
                    percent_of_class NUMERIC,
                    voting_sole BIGINT,
                    voting_shared BIGINT,
                    shares_dispo_sole BIGINT,
                    shares_dispo_shared BIGINT
                )""")
        
        csv_io = io.StringIO()
        df.to_csv(csv_io, index=False)
        csv_io.seek(0)
        # COPY raw CSV into staging
        with conn.cursor() as cur:
            with cur.copy(f"COPY {staging_table} FROM STDIN WITH CSV HEADER") as copy:
                copy.write(csv_io.read())
        conn.commit()
        merge_13g_staging_to_schema(staging_table, conn)
        conn.commit()
        print(f"Saved {len(df)} 13G rows to DB {staging_table} and merged")

    except Exception as e:
        print("Error during COPY for 13G:", e)
        conn.rollback()
        raise
    finally:
        conn.close()

# verifications
#  psql -d edgar_db -c "SELECT COUNT(*) FROM staging_13f;"
# psql -d edgar_db -c "SELECT accession_number, report_date, primary_doc_url FROM filings WHERE accession_number IN (SELECT DISTINCT accession_number FROM staging_13f) ORDER BY accession_number LIMIT 6;"
## example join (filings -> holdings_raw -> securities) for sample accession:
# psql -d edgar_db -c "SELECT f.accession_number, i.cusip, i.issuer_name, h.shares_owned, h.share_type FROM filings f JOIN holdings_raw h ON f.filing_id = h.filing_id JOIN securities i ON i.issuer_id = h.issuer_id WHERE f.accession_number = '000108514625004804' LIMIT 5;"

## duplicate key violations (should be 0)
# psql -d edgar_db -c "SELECT filing_id, issuer_id, share_type, COUNT(*) FROM holdings_raw GROUP BY filing_id, issuer_id, share_type HAVING COUNT(*)>1;"