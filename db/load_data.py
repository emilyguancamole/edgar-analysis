from connect_db import get_conn

def _show_db_info(conn, cur):
    cur.execute("SELECT current_database(), current_user, current_schema();")
    db, user, schema = cur.fetchone()
    print(f"DB={db} user={user} schema={schema}")

def _count(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table};")
    return cur.fetchone()[0]

### Load data
def load_13f_csv_to_staging(csv_path, staging_table, conn):
    with conn.cursor() as cur:
        # _show_db_info(conn, cur)
        try:
            # Drop/create staging for each run
            cur.execute(f"DROP TABLE IF EXISTS {staging_table};")
            cur.execute(f"""
                CREATE TABLE {staging_table} (
                    accession_number TEXT,
                    report_date DATE,
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
        
            # COPY raw CSV into staging
            with open(csv_path, "r", encoding="utf-8") as f:
                # COPY FROM copies data from a file to a table (appending)
                with cur.copy(f"COPY {staging_table} FROM STDIN WITH CSV HEADER") as copy:
                    copy.write(f.read())
        except Exception as e:
            print("Error during COPY for 13F:", e)
            raise

        conn.commit()
        print(f"Loaded {csv_path} into {staging_table}, rows={_count(cur, staging_table)}")



def load_13g_csv_to_staging(csv_path, staging_table, conn):
    """Load 13G CSV data into a staging table."""
    with conn.cursor() as cur:
        try:
            # drop/create staging for each run
            cur.execute(f"DROP TABLE IF EXISTS {staging_table};")
            # todo how to connect to fund / identify name of filer w/ an id/cik
            cur.execute(f"""
                CREATE TABLE {staging_table} (
                    accession_number TEXT,
                    primary_doc TEXT,
                    cik TEXT,
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
        
            # COPY raw CSV into staging
            with open(csv_path, "r", encoding="utf-8") as f:
                # COPY FROM copies data from a file to a table (appending)
                with cur.copy(f"COPY {staging_table} FROM STDIN WITH CSV HEADER") as copy:
                    copy.write(f.read())

            conn.commit()
            print(f"Loaded {csv_path} into {staging_table}, rows={_count(cur, staging_table)}")

        except Exception as e:
            print("Error during COPY for 13G:", e)
            raise



def merge_13f_staging_to_schema(staging_table, conn):
    with conn.cursor() as cur:
        _show_db_info(conn, cur)
        # Insert issuers, dedup on cusip
        cur.execute(f"""
            INSERT INTO issuers (issuer_name, cusip, figi)
            SELECT DISTINCT issuer, cusip, figi
            FROM {staging_table}
            ON CONFLICT (cusip) DO NOTHING;
        """)
        conn.commit()
        print("issuers rows:", _count(cur, "issuers"))

        # Insert filings
        cur.execute(f"""
            INSERT INTO filings (accession_number, report_date, cik,filing_type, primary_doc_url)
            SELECT DISTINCT accession_number, report_date, '13F', primary_doc_url
            FROM {staging_table}
            ON CONFLICT (accession_number) DO NOTHING;
        """)
        conn.commit()
        print("filings rows:", _count(cur, "filings"))

        # Insert holdings_raw
        cur.execute(f"""
            INSERT INTO holdings_raw (
                filing_id, issuer_id, shares_owned, share_type, value_dollar,
                discretion, voting_sole, voting_shared, voting_none
            )
            SELECT f.filing_id, i.issuer_id, s.shares_owned, s.share_type, s.value_dollar,
                   s.discretion, s.voting_sole, s.voting_shared, s.voting_none
            FROM {staging_table} s
            JOIN filings f ON f.accession_number = s.accession_number
            JOIN issuers i ON i.cusip = s.cusip;
        """)
        conn.commit()
        print("holdings_raw rows:", _count(cur, "holdings_raw"))


def merge_13g_staging_to_schema(staging_table, conn):
    """Merge data from 13G staging table into main schema tables."""
    with conn.cursor() as cur:
        # Insert issuers, dedup on cusip
        cur.execute(f"""
            INSERT INTO issuers (issuer_name, cusip)
            SELECT DISTINCT issuer, cusip
            FROM {staging_table}
            ON CONFLICT (cusip) DO NOTHING;
        """)
        conn.commit()
        print("issuers rows:", _count(cur, "issuers"))


        # Insert filings
        cur.execute(f"""
            INSERT INTO filings (accession_number, report_date, filing_type, primary_doc_url)
            SELECT DISTINCT accession_number, cik, report_date, '13G', primary_doc
            FROM {staging_table}
            ON CONFLICT (accession_number) DO NOTHING;
        """)
        conn.commit()
        print("filings rows:", _count(cur, "filings"))

        # Insert holdings_raw
        cur.execute(f"""
            INSERT INTO holdings_raw (
                filing_id, issuer_id, shares_owned,percent_of_class,voting_sole,voting_shared,shares_dispo_sole,shares_dispo_shared
            )
            SELECT f.filing_id, i.issuer_id, s.shares_owned,s.percent_of_class,s.voting_sole,s.voting_shared,s.shares_dispo_sole,s.shares_dispo_shared
            FROM {staging_table} s
            JOIN filings f ON f.accession_number = s.accession_number
            JOIN issuers i ON i.cusip = s.cusip;
        """)
        conn.commit()
        print("holdings_raw rows:", _count(cur, "holdings_raw"))


def load_funds(conn):
    #! only a few funds, so hardcode for now
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO funds (fund_name, cik)
            VALUES
                ('PRIMECAP Management CO/CA', 0000763212)
            ON CONFLICT (cik) DO NOTHING;
        """)

if __name__ == "__main__":
    conn = get_conn()
    load_13f_csv_to_staging("./data/extracted_13f.csv", "staging_13f", conn)
    merge_13f_staging_to_schema("staging_13f", conn)
    load_13g_csv_to_staging("./data/extracted_13g.csv", "staging_13g", conn)
    merge_13g_staging_to_schema("staging_13g", conn)
    load_funds(conn)
    print("Data loaded successfully.")
    conn.commit()
    conn.close()