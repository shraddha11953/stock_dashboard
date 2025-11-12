# app/crud.py
from sqlalchemy.orm import Session
from app import models
from datetime import date, timedelta
from typing import List, Dict
from sqlalchemy import func, desc


# ✅ 1. Get list of all distinct company symbols
def get_companies(db: Session):
    q = db.query(models.Stock.symbol).distinct().order_by(models.Stock.symbol.asc()).all()
    return [row[0] for row in q]


# ✅ 2. Get last N days of data for a given stock symbol (default = 30 days)
def get_last_n_days(db: Session, symbol: str, n: int = 30):
    return (
        db.query(models.Stock)
        .filter(models.Stock.symbol == symbol)
        .order_by(models.Stock.date.desc())
        .limit(n)
        .all()
    )


# ✅ 3. Summary data for dashboard
def get_summary(db: Session, symbol: str):
    rows = (
        db.query(models.Stock)
        .filter(models.Stock.symbol == symbol)
        .order_by(models.Stock.date.desc())
        .limit(252)
        .all()
    )
    if not rows:
        return None

    highs = [r.high for r in rows]
    lows = [r.low for r in rows]
    closes = [r.close for r in rows]
    avg_close = round(sum(closes) / len(closes), 2)

    return {
        "symbol": symbol,
        "week52_high": max(highs),
        "week52_low": min(lows),
        "avg_close": avg_close,
    }


# ✅ 4. Get most recent date available
def get_latest_date(db: Session):
    row = db.query(func.max(models.Stock.date)).one()
    return row[0]


# ✅ 5. Get top gainers and losers (for given or latest date)
def get_top_movers(db: Session, on_date=None, top: int = 5):
    # Get latest date if not provided
    if on_date is None:
        on_date = db.query(models.Stock.date).order_by(models.Stock.date.desc()).first()
        if on_date:
            on_date = on_date[0]
        else:
            return {"date": None, "top_gainers": [], "top_losers": []}

    # Fetch all stocks for that date
    stocks = db.query(models.Stock).filter(models.Stock.date == on_date).all()
    if not stocks:
        return {"date": on_date.isoformat(), "top_gainers": [], "top_losers": []}

    # Calculate percentage change
    for s in stocks:
        s.change_pct = ((s.close - s.open) / s.open) * 100 if s.open else 0

    gainers = sorted(stocks, key=lambda x: x.change_pct, reverse=True)[:top]
    losers = sorted(stocks, key=lambda x: x.change_pct)[:top]

    return {
        "date": on_date.isoformat(),
        "top_gainers": [{"symbol": g.symbol, "change_pct": round(g.change_pct, 2)} for g in gainers],
        "top_losers": [{"symbol": l.symbol, "change_pct": round(l.change_pct, 2)} for l in losers],
    }


# ✅ 6. Get all closing prices (oldest → newest) for frontend charts
def get_all_closes(db: Session, symbol: str):
    rows = (
        db.query(models.Stock)
        .filter(models.Stock.symbol == symbol)
        .order_by(models.Stock.date.asc())
        .all()
    )
    return [
        {"date": r.date.isoformat(), "close": round(r.close, 2)}
        for r in rows
    ]


# ✅ 7. Helper: get moving average (for graphs)
def get_moving_average(db: Session, symbol: str, window: int = 5):
    rows = get_all_closes(db, symbol)
    closes = [r["close"] for r in rows]
    dates = [r["date"] for r in rows]

    if len(closes) < window:
        return []

    moving_avg = []
    for i in range(window - 1, len(closes)):
        avg = sum(closes[i - window + 1 : i + 1]) / window
        moving_avg.append({"date": dates[i], "ma": round(avg, 2)})

    return moving_avg
