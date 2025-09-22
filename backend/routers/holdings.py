from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import select, Session
from sqlalchemy import func, desc, asc
from typing import Optional
from datetime import date as date_cls

from db.models import HoldingsTS, Security
from db.connect_db import get_session

# HOLDINGS ENDPOINTS

router = APIRouter(
    prefix="/holdings",
    tags=["holdings"],
    responses={404: {"description": "Not found"}}
)


@router.get("/")
def read_root():
    return {"message": "Hello from holdings"}


@router.get("/shares")
def get_shares(
    cik: str,
    date: Optional[str] = None,
    page: int = 1,
    limit: int = 200,
    sort_field: Optional[str] = Query(None, description="Field to sort by, e.g. shares_owned"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    session: Session = Depends(get_session),
):
    """
    Returns rows for a fund for a single date (default latest):
      - date
      - issuer_id, issuer_name, cusip
      - shares_owned, shares_change, shares_change_pct
    Pagination via page & limit.
    
    example: /holdings/shares?cik=0001166559&date=2023-11-30&page=1
    """

    # determine target date (parse iso date if provided)
    target_date: Optional[date_cls]
    if date: # parse specified date
        try:
            target_date = date_cls.fromisoformat(date)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date, expected YYYY-MM-DD")
    else:
        stmt_max = select(func.max(HoldingsTS.date)).where(HoldingsTS.fund_id == cik)
        print(f"DEBUG: Looking for fund_id = '{cik}'")
        print(f"DEBUG stmt_max: {stmt_max}")
        latest_row = session.exec(stmt_max).one_or_none()
        print(f"DEBUG latest_row result (date): {latest_row}")

        if not latest_row:
            # DEBUG check what fund_ids actually exist
            debug_stmt = select(func.distinct(HoldingsTS.fund_id)).limit(10)
            existing_funds = session.exec(debug_stmt).all()
            print(f"DEBUG: Existing fund_ids in holdings_ts: {existing_funds}")
            raise HTTPException(status_code=404, detail=f"No holdings_ts found for CIK {cik}")
        target_date = latest_row

    # compute total count for pagination
    stmt_count = select(func.count()).where(HoldingsTS.fund_id == cik, HoldingsTS.date == target_date)
    total = session.exec(stmt_count).one()

    # build base select
    stmt = (
        select(HoldingsTS, Security)
        .join(Security, HoldingsTS.issuer_id == Security.issuer_id)
        .where(HoldingsTS.fund_id == cik, HoldingsTS.date == target_date)
    )

    # optional sorting
    if sort_field:
        sort_col = None
        if sort_field == "shares_owned":
            sort_col = HoldingsTS.shares_owned
        elif sort_field == "shares_change":
            sort_col = HoldingsTS.shares_change
        elif sort_field == "shares_change_pct":
            sort_col = HoldingsTS.shares_change_pct
        elif sort_field == "issuer_name":
            sort_col = Security.issuer_name

        if sort_col is not None:
            stmt = stmt.order_by(asc(sort_col) if sort_order == "asc" else desc(sort_col))

    # pagination
    stmt = stmt.limit(limit).offset(max(0, (page - 1)) * limit)
    pairs = session.exec(stmt).all()  # list of (HoldingsTS for the date, Security) tuples

    # Collect data to output rows
    out_rows = []
    for holding, sec in pairs:
        shares_owned = int(holding.shares_owned or 0)
        shares_change = None if holding.shares_change is None else int(holding.shares_change)
        shares_change_pct = None
        if holding.shares_change_pct is not None:
            try:
                shares_change_pct = float(holding.shares_change_pct) # use change fields stored in holdings_ts 
            except Exception:
                shares_change_pct = None

        uid = f"{cik}|{holding.issuer_id}|{target_date.isoformat()}"
        out_rows.append({
            "id": uid,
            "date": target_date.isoformat(),
            "issuer_id": holding.issuer_id,
            "issuer_name": sec.issuer_name,
            "cusip": sec.cusip,
            "shares_owned": shares_owned,
            "shares_change": shares_change,
            "shares_change_pct": shares_change_pct,
        })

    return {
        "cik": cik,
        "date": target_date.isoformat(),
        "page": page,
        "limit": limit,
        "total": total,
        "rows": out_rows, # list of dicts, each dict is 1 holding at the date
    }


# TODO: ownership endpoints, filtering, sorting