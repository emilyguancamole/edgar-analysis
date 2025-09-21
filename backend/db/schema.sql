-- funds (one row per reporting manager/filer)
CREATE TABLE funds (
    fund_id SERIAL PRIMARY KEY,
    fund_name TEXT NOT NULL,
    irs_id TEXT
);

-- securities (one row per security/issuer)
CREATE TABLE securities (
    issuer_id SERIAL PRIMARY KEY,
    issuer_name TEXT NOT NULL,
    cusip TEXT UNIQUE NOT NULL,
    figi TEXT
);

-- filings (one row per submission)
CREATE TABLE filings (
    filing_id SERIAL PRIMARY KEY,
    accession_number TEXT UNIQUE NOT NULL,
    fund_id INT REFERENCES funds(fund_id),
    filing_type TEXT CHECK (filing_type IN ('13F','13G')),
    report_date DATE NOT NULL,
    primary_doc TEXT
);

-- raw holdings (direct parse from filings)
CREATE TABLE holdings_raw (
    id SERIAL PRIMARY KEY,
    filing_id INT REFERENCES filings(filing_id),
    issuer_id INT REFERENCES securities(issuer_id),
    value_dollar BIGINT,
    shares_owned BIGINT,
    share_type TEXT,
    discretion TEXT,
    voting_sole BIGINT,
    voting_shared BIGINT,
    voting_none BIGINT,
    percent_of_class NUMERIC,
    investment_discretion TEXT
);

-- normalized time series (for queries & dashboards)
CREATE TABLE holdings_ts (
    fund_id INT REFERENCES funds(fund_id),
    issuer_id INT REFERENCES securities(issuer_id),
    date DATE NOT NULL,
    shares_owned BIGINT,
    shares_change BIGINT,
    shares_change_pct NUMERIC,
    PRIMARY KEY(fund_id, issuer_id, date)
);
SELECT create_hypertable('holdings_ts', 'date');

-- prices (optional external market data)
CREATE TABLE prices (
    issuer_id INT REFERENCES securities(issuer_id),
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    dividend NUMERIC,
    PRIMARY KEY(issuer_id, date)
);
SELECT create_hypertable('prices', 'date');