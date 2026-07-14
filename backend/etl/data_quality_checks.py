"""
data_quality_checks.py
-----------------------
Standalone version of the data quality checks originally embedded in
airflow/dags/nse_pipeline.py, for use in the GitHub Actions daily-etl
workflow (which doesn't run Airflow).

Fails (non-zero exit code) if the scrape/load produced something
structurally wrong. Thresholds are deliberately loose on ticker count
(NSE occasionally suspends or delists a counter) but strict on the
things that would indicate a broken scrape rather than a normal market
event.

Usage:
    python etl/data_quality_checks.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.session import SessionLocal
from app.db.models import DimTicker, FactDailyPrice, FactMarketIndex


def run_data_quality_checks():
    session = SessionLocal()
    try:
        ticker_count = session.query(DimTicker).count()
        assert ticker_count >= 55, (
            f"Expected at least 55 listed tickers, found {ticker_count} - "
            "the scraper may have parsed a malformed page."
        )

        latest_date = session.query(FactDailyPrice.trade_date).order_by(
            FactDailyPrice.trade_date.desc()
        ).first()
        assert latest_date is not None, "No price rows loaded at all - scrape or load likely failed silently."

        price_rows_today = session.query(FactDailyPrice).filter_by(trade_date=latest_date[0]).count()
        assert price_rows_today >= 40, (
            f"Only {price_rows_today} price rows for {latest_date[0]} - "
            "expected most of the ~67 listed securities to have a row (even if untraded/null price)."
        )

        bad_prices = session.query(FactDailyPrice).filter(
            FactDailyPrice.close_price < 0
        ).count()
        assert bad_prices == 0, f"Found {bad_prices} negative prices - scraper likely mis-parsed a column."

        nasi_rows = session.query(FactMarketIndex).filter_by(index_name="NASI").count()
        assert nasi_rows >= 1, "No NASI index rows loaded at all."

        print(f"✅ Data quality OK: {ticker_count} tickers, {price_rows_today} price rows "
              f"for {latest_date[0]}, {nasi_rows} NASI index rows.")
    finally:
        session.close()


if __name__ == "__main__":
    try:
        run_data_quality_checks()
    except AssertionError as e:
        print(f"❌ Data quality check failed: {e}", file=sys.stderr)
        sys.exit(1)
