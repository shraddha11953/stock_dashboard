
import os
import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from sqlalchemy.orm import Session
from app import db, models, crud, data_fetcher
from app.scheduler import start_scheduler

# LOGGING SETUP 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FASTAPI APP 
app = FastAPI(title="Stock Data Intelligence Dashboard")

# Start background scheduler (daily data refresh)
start_scheduler()

# Create database tables if not exist
models.Base.metadata.create_all(bind=db.engine)

# STATIC FILES 
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static"
)

# DATABASE DEPENDENCY
def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

#  ROUTES 

# List all companies
@app.get("/companies", response_model=List[str])
def list_companies(session: Session = Depends(get_db)):
    return crud.get_companies(session)

# Get stock data 
@app.get("/data/{symbol}")
def get_data_old(symbol: str, days: int = Query(30, ge=1, le=365), session: Session = Depends(get_db)):
    rows = crud.get_last_n_days(session, symbol, n=days)
    if not rows:
        raise HTTPException(status_code=404, detail="Symbol not found or no data")
    return [
        {
            "date": r.date.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "adj_close": r.adj_close,
            "volume": r.volume,
            "daily_return": r.daily_return,
            "ma_7": r.ma_7,
        }
        for r in reversed(rows)
    ]

# API for company list 
@app.get("/api/companies")
def api_companies(session: Session = Depends(get_db)):
    return {"companies": crud.get_companies(session)}

#  API for data 
@app.get("/api/data")
def api_data(symbol: str, days: int = Query(90, ge=1, le=365), session: Session = Depends(get_db)):
    rows = crud.get_last_n_days(session, symbol, n=days)
    if not rows:
        raise HTTPException(status_code=404, detail="Symbol not found or no data")
    data = [
        {
            "date": r.date.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "adj_close": r.adj_close,
            "volume": r.volume,
            "daily_return": r.daily_return,
            "ma_7": r.ma_7,
        }
        for r in reversed(rows)
    ]
    return {"symbol": symbol, "data": data}

# Manual data refresh 
@app.post("/refresh")
def refresh_data(background_tasks: BackgroundTasks, symbols: Optional[List[str]] = None):
    """
    Trigger a manual refresh. If symbols is None, refresh the default stock list.
    Runs fetch_and_store in background.
    """
    if symbols is None:
        symbols = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS"]

    background_tasks.add_task(data_fetcher.fetch_and_store, symbols, "1y")
    logger.info(f"Manual refresh started for {symbols}")
    return {"status": "refresh started", "symbols": symbols}

#  dashboard HTML
@app.get("/", response_class=FileResponse)
def read_root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "dashboard.html"))
