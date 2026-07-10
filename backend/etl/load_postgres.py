"""
load_postgres.py
-----------------
Loads NSE data into Postgres. Two data sources, handled differently:

  1. dim_ticker - loaded once from the static seed (data/dim_ticker.csv),
     since the ticker/name/sector mapping doesn't change often.

  2. fact_daily_price / fact_market_index / fact_market_summary - loaded
     from whatever the scraper most recently wrote to data/scraped/. If
     that directory is empty (i.e. you haven't run scrape_nse.py for real
     yet), falls back to the seed snapshots (data/nasi_index_seed.csv,
     data/nse_gainers_losers_seed.csv, data/nse_daily_summary_seed.csv) so
     the pipeline is runnable immediately after unzipping, before you've
     set up live scraping.

This is intentionally idempotent per trade_date: re-running for a date
that's already loaded replaces that date's rows rather than duplicating.
"""

import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.models import Base, DimTicker, FactDailyPrice, FactMarketIndex, FactMarketSummary, ETLRunLog
from app.db.session import engine, SessionLocal

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SCRAPED_DIR = DATA_DIR / "scraped"


def load_dim_ticker(session: Session) -> dict:
    df = pd.read_csv(DATA_DIR / "dim_ticker.csv")
    name_to_id = {}
    for row in df.itertuples():
        existing = session.query(DimTicker).filter_by(ticker=row.ticker).first()
        if existing:
            existing.name = row.name
            existing.sector_approx = row.sector_approx
            name_to_id[row.ticker] = existing.ticker_id
        else:
            rec = DimTicker(ticker=row.ticker, name=row.name, sector_approx=row.sector_approx)
            session.add(rec)
            session.flush()
            name_to_id[row.ticker] = rec.ticker_id
    session.commit()
    return name_to_id


def _latest_scraped_file(prefix: str) -> Path | None:
    if not SCRAPED_DIR.exists():
        return None
    matches = sorted(SCRAPED_DIR.glob(f"{prefix}_*.csv"), reverse=True)
    return matches[0] if matches else None


def load_daily_prices(session: Session, ticker_map: dict) -> int:
    listings_file = _latest_scraped_file("listings")
    if listings_file:
        df = pd.read_csv(listings_file)
        trade_date = datetime.strptime(listings_file.stem.split("_", 1)[1], "%Y-%m-%d").date()
        source = f"scraped: {listings_file.name}"
    else:
        # Fall back to the gainers/losers seed - it's real data, just partial
        # (only the 12 tickers that appeared in the sidebar, not all 67).
        df = pd.read_csv(DATA_DIR / "nse_gainers_losers_seed.csv")
        df = df.rename(columns={"close_price": "close_price"})
        trade_date = datetime.strptime(str(df["trade_date"].iloc[0]), "%Y-%m-%d").date()
        source = "seed: nse_gainers_losers_seed.csv (partial - 12 tickers only)"

    session.query(FactDailyPrice).filter_by(trade_date=trade_date).delete()
    rows = 0
    for row in df.itertuples():
        if row.ticker not in ticker_map:
            continue  # unmapped ticker - shouldn't happen if dim_ticker.csv is kept in sync
        volume = getattr(row, "volume", None)
        price = getattr(row, "close_price", None)
        change_abs = getattr(row, "change_abs", None) if hasattr(row, "change_abs") else None
        change_pct = getattr(row, "change_pct", None) if hasattr(row, "change_pct") else None

        session.add(FactDailyPrice(
            ticker_id=ticker_map[row.ticker],
            trade_date=trade_date,
            volume=None if pd.isna(volume) else int(volume),
            close_price=None if pd.isna(price) else float(price),
            change_abs=None if pd.isna(change_abs) else float(change_abs),
            change_pct=None if pd.isna(change_pct) else float(change_pct),
        ))
        rows += 1
    session.commit()
    print(f"Loaded {rows} daily price rows for {trade_date} (source: {source})")
    return rows


def load_market_index(session: Session) -> int:
    index_file = _latest_scraped_file("nasi")
    if index_file:
        df = pd.read_csv(index_file)
    else:
        df = pd.read_csv(DATA_DIR / "nasi_index_seed.csv")

    rows = 0
    for row in df.itertuples():
        trade_date = datetime.strptime(str(row.trade_date), "%Y-%m-%d").date()
        session.query(FactMarketIndex).filter_by(index_name=row.index_name, trade_date=trade_date).delete()
        session.add(FactMarketIndex(
            index_name=row.index_name,
            trade_date=trade_date,
            close_value=float(row.close_value),
            change_abs=None if pd.isna(getattr(row, "change_abs", None)) else float(row.change_abs),
            change_pct=None if pd.isna(getattr(row, "change_pct", None)) else float(row.change_pct),
            ytd_pct=None if pd.isna(getattr(row, "ytd_pct", None)) else float(row.ytd_pct),
            source_url=getattr(row, "source_url", None),
            source_note=getattr(row, "source_note", None),
        ))
        rows += 1
    session.commit()
    return rows


def load_market_summary(session: Session) -> int:
    summary_file = _latest_scraped_file("summary")
    if summary_file:
        df = pd.read_csv(summary_file)
    else:
        df = pd.read_csv(DATA_DIR / "nse_daily_summary_seed.csv")

    rows = 0
    for row in df.itertuples():
        trade_date = datetime.strptime(str(row.trade_date), "%Y-%m-%d").date()
        session.query(FactMarketSummary).filter_by(trade_date=trade_date).delete()
        session.add(FactMarketSummary(
            trade_date=trade_date,
            total_shares_traded=int(row.total_shares_traded) if not pd.isna(getattr(row, "total_shares_traded", None)) else None,
            total_deals=int(row.total_deals) if not pd.isna(getattr(row, "total_deals", None)) else None,
            market_value_kes=float(row.market_value_kes) if not pd.isna(getattr(row, "market_value_kes", None)) else None,
            market_cap_kes=float(row.market_cap_kes) if not pd.isna(getattr(row, "market_cap_kes", None)) else None,
            gainers_count=int(row.gainers_count) if not pd.isna(getattr(row, "gainers_count", None)) else None,
            losers_count=int(row.losers_count) if not pd.isna(getattr(row, "losers_count", None)) else None,
            listed_companies_traded=int(row.listed_companies_traded) if not pd.isna(getattr(row, "listed_companies_traded", None)) else None,
            source_url=getattr(row, "source_url", None),
        ))
        rows += 1
    session.commit()
    return rows


def log_run(session: Session, task_name: str, rows: int, status: str, detail: str = ""):
    session.add(ETLRunLog(run_date=date.today(), task_name=task_name, rows_loaded=rows, status=status, detail=detail))
    session.commit()


def run():
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        ticker_map = load_dim_ticker(session)
        log_run(session, "load_dim_ticker", len(ticker_map), "success")

        n = load_daily_prices(session, ticker_map)
        log_run(session, "load_daily_prices", n, "success")

        n = load_market_index(session)
        log_run(session, "load_market_index", n, "success")

        n = load_market_summary(session)
        log_run(session, "load_market_summary", n, "success")

        print("Postgres load complete.")
    except Exception as e:
        log_run(session, "load_postgres", 0, "failed", str(e))
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
