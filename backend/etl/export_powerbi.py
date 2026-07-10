"""
export_powerbi.py
-------------------
Exports flat CSVs for Power BI - same pattern as the cost-of-living
project. See powerbi/README.md for direct-Postgres vs CSV-import options.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.session import engine

OUT_DIR = Path(__file__).resolve().parents[2] / "powerbi" / "exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def export():
    stocks_query = """
        SELECT t.ticker, t.name, t.sector_approx, p.trade_date, p.volume,
               p.close_price, p.change_abs, p.change_pct
        FROM dim_ticker t
        JOIN fact_daily_price p ON p.ticker_id = t.ticker_id
        ORDER BY p.trade_date, p.change_pct DESC
    """
    stocks = pd.read_sql(stocks_query, engine)
    stocks.to_csv(OUT_DIR / "stock_prices.csv", index=False)

    index_history = pd.read_sql("SELECT * FROM fact_market_index ORDER BY trade_date", engine)
    index_history.to_csv(OUT_DIR / "index_history.csv", index=False)

    market_summary = pd.read_sql("SELECT * FROM fact_market_summary ORDER BY trade_date", engine)
    market_summary.to_csv(OUT_DIR / "market_summary.csv", index=False)

    run_log = pd.read_sql("SELECT * FROM etl_run_log ORDER BY id DESC LIMIT 100", engine)
    run_log.to_csv(OUT_DIR / "etl_run_log.csv", index=False)

    print(f"Exported {len(stocks)} stock-price rows, {len(index_history)} index rows, "
          f"{len(market_summary)} market summary rows to {OUT_DIR}")


if __name__ == "__main__":
    export()
