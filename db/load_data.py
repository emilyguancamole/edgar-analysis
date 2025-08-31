## todo Load data from CSV to DB

from db.schema import Fund, Issuer


def get_or_create_fund(session, name, irs_id):
    """ Prevent duplicate funds when loading filings """
    fund = session.query(Fund).filter_by(name=name, irs_id=irs_id).first()
    if fund:
        return fund
    fund = Fund(name=name, irs_id=irs_id)
    session.add(fund)
    session.commit()
    return fund

def get_or_create_issuer(session, name, cusip=None, figi=None):
    """ Prevent duplicate issuers when loading holdings """
    issuer = None
    if cusip:
        issuer = session.query(Issuer).filter_by(cusip=cusip).first()
    if not issuer:
        issuer = Issuer(name=name, cusip=cusip, figi=figi)
        session.add(issuer)
        session.commit()
    return issuer
