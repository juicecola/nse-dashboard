"""
nse_pipeline.py
----------------
Airflow DAG for the NSE Kenya market dashboard.

    scrape_nse
        |
        v
    load_postgres    (dim_ticker, fact_daily_price, fact_market_index, fact_market_summary)
        |
        v
    data_quality_checks
        |
        v
    export_static_json    (refresh backend/app/static_data/* for the API fallback)
        |
        v
    export_powerbi_csv

Schedule: weekdays at 16:00 Nairobi time (13:00 UTC), after the NSE closes
at 15:00 Nairobi - this is a genuinely time-sensitive schedule, unlike the
cost-of-living project's weekly cadence, because the source itself only
has new data once per trading day.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "nse-dashboard",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

BACKEND_DIR = "/opt/airflow/project/backend"

with DAG(
    dag_id="nse_pipeline",
    description="Scrape, load, validate, and export NSE Kenya market data",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="0 13 * * 1-5",  # 13:00 UTC = 16:00 Nairobi, weekdays only - the market's own schedule
    catchup=False,
    is_paused_upon_creation=True,
    tags=["nse-dashboard", "etl", "finance"],
) as dag:

    scrape_nse = BashOperator(
        task_id="scrape_nse",
        bash_command=f"cd {BACKEND_DIR} && python etl/scrape_nse.py",
    )

    load_postgres = BashOperator(
        task_id="load_postgres",
        bash_command=f"cd {BACKEND_DIR} && python etl/load_postgres.py",
    )

    def _run_data_quality_checks():
        """Fails the run if the scrape/load produced something structurally
        wrong. Thresholds are deliberately loose on ticker count (NSE
        occasionally suspends or delists a counter) but strict on the
        things that would indicate a broken scrape rather than a normal
        market event."""
        import sys
        sys.path.insert(0, BACKEND_DIR)
        from app.db.session import SessionLocal
        from app.db.models import DimTicker, FactDailyPrice, FactMarketIndex

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

            print(f"Data quality OK: {ticker_count} tickers, {price_rows_today} price rows "
                  f"for {latest_date[0]}, {nasi_rows} NASI index rows.")
        finally:
            session.close()

    data_quality_checks = PythonOperator(
        task_id="data_quality_checks",
        python_callable=_run_data_quality_checks,
    )

    export_static_json = BashOperator(
        task_id="export_static_json",
        bash_command=f"cd {BACKEND_DIR} && python etl/build_static_export.py",
    )

    export_powerbi_csv = BashOperator(
        task_id="export_powerbi_csv",
        bash_command=f"cd {BACKEND_DIR} && python etl/export_powerbi.py",
    )

    scrape_nse >> load_postgres >> data_quality_checks >> export_static_json >> export_powerbi_csv
