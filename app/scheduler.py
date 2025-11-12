# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.data_fetcher import fetch_and_store
import atexit

def scheduled_job():
    print(f"[{datetime.now()}] 🔁 Running daily stock data refresh...")
    symbols = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS"]
    try:
        fetch_and_store(symbols, period="1y")
        print(" Data refresh complete!")
    except Exception as e:
        print(" Error during scheduled fetch:", e)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(scheduled_job, 'cron', hour=9, minute=0)  # every day at 9:00 AM
    scheduler.start()
    print("🕒 Scheduler started — daily data update enabled at 9:00 AM")
    atexit.register(lambda: scheduler.shutdown())
