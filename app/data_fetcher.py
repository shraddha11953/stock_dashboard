import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session
from app import models, db
from datetime import datetime
import numpy as np

def fetch_and_store(symbols, period="1y"):
    """
    Fetch historical stock data for given symbols and store/update in SQLite DB.
    Works even if yfinance returns MultiIndex or renamed columns.
    """
    engine = db.engine
    models.Base.metadata.create_all(bind=engine)
    session = db.SessionLocal()

    try:
        for sym in symbols:
            print(f"\nFetching {sym} ...")
            df = yf.download(sym, period=period, progress=False)

            if df.empty:
                print(f"No data for {sym}")
                continue

            df = df.reset_index()

            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(c).strip().lower() for c in col if c]).replace(" ", "_") for col in df.columns]
            else:
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

           
            possible_close_cols = [c for c in df.columns if "close" in c]
            possible_open_cols = [c for c in df.columns if "open" in c]
            possible_high_cols = [c for c in df.columns if "high" in c]
            possible_low_cols = [c for c in df.columns if "low" in c]
            possible_volume_cols = [c for c in df.columns if "volume" in c]

            if not possible_close_cols:
                print(f" missing 'close' column  for {sym}")
                continue

            # pick the first matching column
            c_close = possible_close_cols[0]
            c_open = possible_open_cols[0] if possible_open_cols else c_close
            c_high = possible_high_cols[0] if possible_high_cols else c_close
            c_low = possible_low_cols[0] if possible_low_cols else c_close
            c_volume = possible_volume_cols[0] if possible_volume_cols else None

            # --- Ensure 'date' column exists ---
            if "date" not in df.columns:
                for c in df.columns:
                    if "date" in c:
                        df.rename(columns={c: "date"}, inplace=True)
                        break

            # --- Compute metrics ---
            df["daily_return"] = (df[c_close] - df[c_open]) / df[c_open]
            df["ma_7"] = df[c_close].rolling(window=7).mean()

            # --- Insert/Update in DB ---
            for _, row in df.iterrows():
                try:
                    rec = models.StockDaily(
                        symbol=sym,
                        date=pd.to_datetime(row["date"]).date(),
                        open=float(row[c_open]),
                        high=float(row[c_high]),
                        low=float(row[c_low]),
                        close=float(row[c_close]),
                        adj_close=float(row.get("adj_close", row[c_close])),
                        volume=float(row.get(c_volume, 0)) if c_volume else 0,
                        daily_return=None if pd.isna(row["daily_return"]) else float(row["daily_return"]),
                        ma_7=None if pd.isna(row["ma_7"]) else float(row["ma_7"]),
                    )
                    session.merge(rec)
                except Exception as e:
                    print(f"Skipping row for {sym} on {row.get('date', 'unknown')}: {e}")

            session.commit()
            print(f" data Stored for {sym}")

    except Exception as e:
        print("Error during fetch:", e)
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    symbols = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS"]
    fetch_and_store(symbols, period="1y")
