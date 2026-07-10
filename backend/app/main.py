import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.session import engine

STATIC_DIR = Path(__file__).resolve().parent / "static_data"

app = FastAPI(
    title="NSE Kenya Market Dashboard API",
    description="Serves Nairobi Securities Exchange price/index data, from Postgres when reachable, "
                "falling back to a static snapshot otherwise.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _db_available() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _load_static(name: str):
    path = STATIC_DIR / name
    if not path.exists():
        raise HTTPException(status_code=500, detail=f"Data file missing: {name}. Run backend/etl/build_static_export.py.")
    with open(path) as f:
        return json.load(f)


@app.get("/api/health")
def health():
    return {"status": "ok", "postgres": _db_available()}


@app.get("/api/stocks")
def stocks():
    """Latest daily price row per ticker (whatever the most recent load covers)."""
    if _db_available():
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT t.ticker, t.name, t.sector_approx, p.trade_date, p.volume,
                       p.close_price, p.change_abs, p.change_pct
                FROM dim_ticker t
                JOIN fact_daily_price p ON p.ticker_id = t.ticker_id
                WHERE p.trade_date = (SELECT MAX(trade_date) FROM fact_daily_price)
                ORDER BY p.change_pct DESC NULLS LAST
            """)).mappings().all()
            if rows:
                return [dict(r) | {"trade_date": str(r["trade_date"])} for r in rows]
    return _load_static("stocks.json")


@app.get("/api/stocks/{ticker}")
def stock_detail(ticker: str):
    all_stocks = stocks()
    match = next((s for s in all_stocks if s["ticker"].lower() == ticker.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    history = []
    if _db_available():
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT p.trade_date, p.close_price, p.change_pct
                FROM fact_daily_price p
                JOIN dim_ticker t ON t.ticker_id = p.ticker_id
                WHERE t.ticker = :ticker
                ORDER BY p.trade_date
            """), {"ticker": match["ticker"]}).mappings().all()
            history = [dict(r) | {"trade_date": str(r["trade_date"])} for r in rows]

    return {**match, "history": history}


@app.get("/api/index/history")
def index_history():
    """NASI index time series - sparse until the scraper has run for a while."""
    if _db_available():
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT index_name, trade_date, close_value, change_abs, change_pct, ytd_pct "
                "FROM fact_market_index ORDER BY trade_date"
            )).mappings().all()
            if rows:
                return [dict(r) | {"trade_date": str(r["trade_date"])} for r in rows]
    return _load_static("index_history.json")


@app.get("/api/market/summary")
def market_summary():
    """Latest end-of-day market-wide summary (shares traded, deals, market cap, gainers/losers)."""
    if _db_available():
        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT * FROM fact_market_summary ORDER BY trade_date DESC LIMIT 1"
            )).mappings().first()
            if row:
                return dict(row) | {"trade_date": str(row["trade_date"])}
    data = _load_static("market_summary.json")
    return data[0] if data else {}


@app.get("/api/market/gainers-losers")
def gainers_losers():
    """Convenience endpoint: splits the latest stocks() result into gainers/losers lists."""
    all_stocks = [s for s in stocks() if s.get("change_pct") is not None]
    gainers = sorted([s for s in all_stocks if s["change_pct"] > 0], key=lambda s: s["change_pct"], reverse=True)
    losers = sorted([s for s in all_stocks if s["change_pct"] < 0], key=lambda s: s["change_pct"])
    return {"gainers": gainers, "losers": losers}


@app.get("/api/etl/run-log")
def etl_run_log():
    if not _db_available():
        raise HTTPException(status_code=503, detail="Postgres not reachable.")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT run_date, task_name, rows_loaded, status, detail FROM etl_run_log ORDER BY id DESC LIMIT 50"
        )).mappings().all()
        return [dict(r) | {"run_date": str(r["run_date"])} for r in rows]
