import pandas as pd
from connect_db import get_conn

def create_tables(conn):
    cur = conn.cursor()

    # drop tables in dependency order; CASCADE removes dependent objects
    cur.execute("DROP TABLE IF EXISTS holdings_ts CASCADE;")
    cur.execute("DROP TABLE IF EXISTS prices CASCADE;")
    cur.execute("DROP TABLE IF EXISTS holdings_raw CASCADE;")
    cur.execute("DROP TABLE IF EXISTS filings CASCADE;")
    cur.execute("DROP TABLE IF EXISTS issuers CASCADE;")
    cur.execute("DROP TABLE IF EXISTS funds CASCADE;")
    print("Dropped existing tables.")

    # create tables
    cur.execute("""
        CREATE TABLE issuers (
            issuer_id serial PRIMARY KEY,
            issuer_name TEXT NOT NULL,
            cusip TEXT UNIQUE NOT NULL,
            figi TEXT
        );"""
    )

    cur.execute("""
        CREATE TABLE funds (
            fund_id SERIAL PRIMARY KEY,
            fund_name TEXT NOT NULL,
            cik NUMERIC UNIQUE
        );"""
    )

    cur.execute("""
        CREATE TABLE filings (
            filing_id SERIAL PRIMARY KEY,
            accession_number TEXT UNIQUE NOT NULL,
            fund_id INT REFERENCES funds(fund_id),
            filing_type TEXT CHECK (filing_type IN ('13F', '13G', '13G/A')),
            report_date DATE NOT NULL,
            primary_doc_url TEXT
        );"""
    )

    cur.execute("""
        CREATE TABLE holdings_raw (
            holding_id SERIAL PRIMARY KEY,
            filing_id INT REFERENCES filings(filing_id),
            issuer_id INT REFERENCES issuers(issuer_id),
            shares_owned BIGINT,
            share_type TEXT,
            value_dollar NUMERIC,
            discretion TEXT,
            voting_sole BIGINT,
            voting_shared BIGINT,
            voting_none BIGINT,
            percent_of_class NUMERIC,
            shares_dispo_sole BIGINT,
            shares_dispo_shared BIGINT
        );"""
    )

    cur.execute("""
        CREATE TABLE holdings_ts (
            fund_id INT REFERENCES funds(fund_id),
            issuer_id INT REFERENCES issuers(issuer_id),
            date DATE NOT NULL,
            shares_owned BIGINT,
            shares_change BIGINT,
            shares_change_pct NUMERIC,
            PRIMARY KEY(fund_id, issuer_id, date)
        );
        SELECT create_hypertable('holdings_ts', 'date');  
        """
    )

    cur.execute("""
        CREATE TABLE prices (
            issuer_id INT REFERENCES issuers(issuer_id),
            date DATE NOT NULL,
            open NUMERIC,
            high NUMERIC,
            low NUMERIC,
            close NUMERIC,
            volume BIGINT,
            dividends NUMERIC,
            PRIMARY KEY(issuer_id, date)
        );
        SELECT create_hypertable('prices', 'date');     
        """ # creates hypertable for prices, with time as date and partition by issuer_id 
    )

if __name__ == "__main__":
    conn = get_conn()
    create_tables(conn)
    print("Schema created successfully.")
    conn.commit()
    conn.close()