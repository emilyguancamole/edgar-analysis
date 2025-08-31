from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, BigInteger, Numeric
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Fund(Base):
    __tablename__ = "funds"
    fund_id = Column(Integer, primary_key=True, autoincrement=True)
    fund_name = Column(String, nullable=False)
    irs_id = Column(String, unique=True)

    filings = relationship("Filing", back_populates="fund") #? back populates is for two way relationship

class Issuer(Base):
    __tablename__ = "issuers"
    issuer_id = Column(Integer, primary_key=True, autoincrement=True)
    issuer_name = Column(String, nullable=False)
    cusip = Column(String, unique=True, nullable=False)
    figi = Column(String, nullable=True)

class Filing(Base):
    __tablename__ = "filings"
    filing_id = Column(Integer, primary_key=True, autoincrement=True)
    fund_id = Column(Integer, ForeignKey("funds.fund_id"), nullable=False)
    filing_type = Column(String, nullable=False) #13F, 13G, 13G/A
    accession_number = Column(String, unique=True, nullable=False)
    report_date = Column(Date, nullable=False)
    primary_doc_url = Column(String, nullable=True)

    fund = relationship("Fund", back_populates="filings")

class HoldingsRaw(Base):
    __tablename__ = "holdings_raw"
    holding_id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("filings.filing_id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuers.issuer_id"), nullable=False)

    shares_owned = Column(BigInteger, nullable=True)
    share_type = Column(String, nullable=True)
    value_dollar = Column(Numeric, nullable=True)  # 13F dollar value
    discretion = Column(String, nullable=True)
    voting_sole = Column(BigInteger, nullable=True)
    voting_shared = Column(BigInteger, nullable=True)
    voting_none = Column(BigInteger, nullable=True)
    percent_of_class = Column(Float, nullable=True)

    filing = relationship("Filing", back_populates="holdings")
    issuer = relationship("Issuer", back_populates="filings") #?