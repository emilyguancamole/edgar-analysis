import pandas as pd
from .connect_db import get_conn

def _show_db_info(conn, cur):
    cur.execute("SELECT current_database(), current_user, current_schema();")
    db, user, schema = cur.fetchone()
    print(f"DB={db} user={user} schema={schema}")

def _count(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table};")
    return cur.fetchone()[0]

### Load data
def load_funds(conn):
    #! only a few funds, so hardcode for now
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO funds (fund_name, cik)
            VALUES
                ('PRIMECAP Management CO/CA', 'CIK0000763212')
            ON CONFLICT (cik) DO NOTHING;
        """)


def merge_13f_staging_to_schema(staging_table, conn):
    with conn.cursor() as cur:
        # Insert issuers, dedup on cusip
        cur.execute(f"""
            INSERT INTO issuers (issuer_name, cusip, figi)
            SELECT DISTINCT issuer, cusip, figi
            FROM {staging_table}
            ON CONFLICT (cusip) DO NOTHING;
        """)
        conn.commit()
        print("issuers rows:", _count(cur, "issuers"))

        # Insert filings with fund_id fk
        cur.execute(f"""
            INSERT INTO filings (accession_number, report_date, filing_type, primary_doc_url, fund_id)
            SELECT DISTINCT
                s.accession_number,
                s.report_date,
                '13F',
                s.primary_doc_url,
                f.cik
            FROM {staging_table} s
            LEFT JOIN funds f
                ON f.cik = s.cik
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
            JOIN issuers i ON i.cusip = s.cusip
            ON CONFLICT (filing_id, issuer_id, share_type) DO NOTHING;
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

        # Insert filings with fund_id fk
        cur.execute(f"""
            INSERT INTO filings (accession_number, report_date, filing_type, primary_doc_url, fund_id)
            SELECT DISTINCT
                s.accession_number,
                s.report_date,
                '13G',
                s.primary_doc,
                f.cik
            FROM {staging_table} s
            LEFT JOIN funds f
                ON f.cik = s.cik
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
            JOIN issuers i ON i.cusip = s.cusip
            ON CONFLICT (filing_id, issuer_id, share_type) DO NOTHING;
        """)
        conn.commit()
        print("holdings_raw rows:", _count(cur, "holdings_raw"))


def build_holdings_ts(conn):
    q = """
        SELECT f.fund_id, h.issuer_id, f.report_date, h.shares_owned
        FROM holdings_raw h
        JOIN filings f ON h.filing_id = f.filing_id
        ORDER BY f.fund_id, h.issuer_id, f.report_date;
    """
    df = pd.read_sql(q, conn)
    # compute changes
    df["shares_change"] = df.groupby(["fund_id", "issuer_id"])["shares_owned"].diff() # compares difference of each element in the group w/ prev
    df["shares_change_pct"] = df.groupby(["fund_id", "issuer_id"])["shares_owned"].pct_change() * 100 # pct_change of each val to prev in the group
    df = df.fillna({'shares_change': 0, 'shares_change_pct': 0})
    rows = df[["fund_id", "issuer_id", "report_date", "shares_owned", "shares_change", "shares_change_pct"]].values.tolist()

    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO holdings_ts (fund_id, issuer_id, date, shares_owned, shares_change, shares_change_pct)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (fund_id, issuer_id, date) DO NOTHING;
            """, rows)
        
    conn.commit()
    print("Inserted data for holdings_ts")


def build_prices(conn):
    """also timeseries"""
    pass

if __name__ == "__main__":
    conn = get_conn()
    # load_funds(conn)
    # load_13f_csv_to_staging("./data/extracted_13f.csv", "staging_13f", conn)
    # merge_13f_staging_to_schema("staging_13f", conn)
    # load_13g_csv_to_staging("./data/extracted_13g.csv", "staging_13g", conn)
    # merge_13g_staging_to_schema("staging_13g", conn)
    build_holdings_ts(conn)
    conn.commit()
    conn.close()