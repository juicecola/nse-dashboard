"""
build_static_export.py
------------------------
Exports the current Postgres contents to flat JSON files, so the FastAPI
app can fall back to them if Postgres isn't reachable - same resilience
pattern as the cost-of-living project.

Run this after load_postgres.py. If you haven't set up Postgres at all yet,
this script also works standalone directly off the seed CSVs (it re-derives
the same join logic without touching the database), so the API has
*something* to serve even before you stand up Postgres.
"""

import json
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUT_DIR = Path(__file__).resolve().parents[1] / "app" / "static_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def try_export_from_postgres() -> bool:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from app.db.session import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            prices = pd.read_sql(text("""
                SELECT t.ticker, t.name, t.sector_approx, p.trade_date, p.volume,
                       p.close_price, p.change_abs, p.change_pct
                FROM dim_ticker t
                JOIN fact_daily_price p ON p.ticker_id = t.ticker_id
                ORDER BY p.change_pct DESC NULLS LAST
            """), conn)
            index_history = pd.read_sql(text(
                "SELECT * FROM fact_market_index ORDER BY trade_date"
            ), conn)
            summary = pd.read_sql(text(
                "SELECT * FROM fact_market_summary ORDER BY trade_date DESC LIMIT 1"
            ), conn)

        if prices.empty:
            return False

        prices["trade_date"] = prices["trade_date"].astype(str)
        index_history["trade_date"] = index_history["trade_date"].astype(str)
        if not summary.empty:
            summary["trade_date"] = summary["trade_date"].astype(str)

        prices.to_json(OUT_DIR / "stocks.json", orient="records")
        index_history.to_json(OUT_DIR / "index_history.json", orient="records")
        summary.to_json(OUT_DIR / "market_summary.json", orient="records")
        print(f"Exported from Postgres: {len(prices)} stock rows, {len(index_history)} index rows.")
        return True
    except Exception as e:
        print(f"Postgres export not available ({e}); falling back to CSV-derived export.")
        return False


def export_from_csv():
    tickers = pd.read_csv(DATA_DIR / "dim_ticker.csv")
    prices = pd.read_csv(DATA_DIR / "nse_gainers_losers_seed.csv")
    prices = prices.merge(tickers, on="ticker", how="left")
    prices = prices.rename(columns={"close_price": "close_price"})
    prices.to_json(OUT_DIR / "stocks.json", orient="records")

    index_history = pd.read_csv(DATA_DIR / "nasi_index_seed.csv")
    index_history.to_json(OUT_DIR / "index_history.json", orient="records")

    summary = pd.read_csv(DATA_DIR / "nse_daily_summary_seed.csv")
    summary.to_json(OUT_DIR / "market_summary.json", orient="records")
    print(f"Exported from CSV seeds: {len(prices)} stock rows (partial - gainers/losers only), "
          f"{len(index_history)} index rows.")


if __name__ == "__main__":
    if not try_export_from_postgres():
        export_from_csv()
