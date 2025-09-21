from typing import Optional
import datetime
from decimal import Decimal

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Numeric, UniqueConstraint

class Security(SQLModel, table=True):
    __tablename__ = "securities"
    issuer_id: Optional[int] = Field(default=None, primary_key=True)
    issuer_name: str = Field(nullable=False)  # same as "issuer_name TEXT NOT NULL"
    cusip: str = Field(nullable=False, unique=True)
    figi: Optional[str] = None

    holdings: list["HoldingRaw"] = Relationship(back_populates="issuer")
    prices: list["Price"] = Relationship(back_populates="issuer")
    holdings_ts: list["HoldingsTS"] = Relationship(back_populates="issuer")


class Fund(SQLModel, table=True):
    __tablename__ = "funds"
    cik: str = Field(primary_key=True)
    fund_name: str = Field(nullable=False)

    filings: list["Filing"] = Relationship(back_populates="fund")
    holdings_ts: list["HoldingsTS"] = Relationship(back_populates="fund")


class Filing(SQLModel, table=True):
    __tablename__ = "filings"

    filing_id: Optional[int] = Field(default=None, primary_key=True)
    accession_number: str = Field(nullable=False, unique=True)
    fund_id: Optional[str] = Field(default=None, foreign_key="funds.cik", index=True)
    filing_type: Optional[str] = Field(default=None)  # DB has a CHECK constraint; keep as str here
    report_date: datetime.date = Field(nullable=False)
    primary_doc_url: Optional[str] = None

    # relationships
    holdings: list["HoldingRaw"] = Relationship(back_populates="filing")
    fund: Optional[Fund] = Relationship(back_populates="filings")


# holdings_raw
class HoldingRaw(SQLModel, table=True):
    __tablename__ = "holdings_raw"
    __table_args__ = (
        UniqueConstraint("filing_id", "issuer_id", "share_type", name="uq_holdings_raw_filing_issuer_sharetype"),
    )

    holding_id: Optional[int] = Field(default=None, primary_key=True)
    filing_id: Optional[int] = Field(default=None, foreign_key="filings.filing_id", index=True)
    issuer_id: Optional[int] = Field(default=None, foreign_key="securities.issuer_id", index=True)
    shares_owned: Optional[int] = None
    share_type: Optional[str] = None
    value_dollar: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    discretion: Optional[str] = None
    voting_sole: Optional[int] = None
    voting_shared: Optional[int] = None
    voting_none: Optional[int] = None
    percent_of_class: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    shares_dispo_sole: Optional[int] = None
    shares_dispo_shared: Optional[int] = None

    # relationships
    filing: Optional[Filing] = Relationship(back_populates="holdings")
    issuer: Optional[Security] = Relationship(back_populates="holdings")


# holdings_ts (time-series aggregated table)
class HoldingsTS(SQLModel, table=True):
    __tablename__ = "holdings_ts"

    fund_id: str = Field(foreign_key="funds.cik", primary_key=True)
    issuer_id: int = Field(foreign_key="securities.issuer_id", primary_key=True)
    date: datetime.date = Field(primary_key=True)
    shares_owned: Optional[int] = None
    shares_change: Optional[int] = None
    shares_change_pct: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))

    fund: Optional[Fund] = Relationship(back_populates="holdings_ts")
    issuer: Optional[Security] = Relationship(back_populates="holdings_ts")


# prices
class Price(SQLModel, table=True):
    __tablename__ = "prices"

    issuer_id: int = Field(foreign_key="securities.issuer_id", primary_key=True)
    date: datetime.date = Field(primary_key=True)
    open: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    high: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    low: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    close: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))
    volume: Optional[int] = None
    dividends: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric))

    issuer: Optional[Security] = Relationship(back_populates="prices")