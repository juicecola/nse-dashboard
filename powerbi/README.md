# Power BI

## Option A — Direct Postgres connection (live refresh)

1. Load data first: `cd backend && python etl/load_postgres.py`
2. Power BI Desktop → **Get Data → More → Database → PostgreSQL database**
3. Server: `localhost:5432`, Database: `nse_dashboard`
4. Credentials: user `nse_dashboard`, password `nse_dashboard`
5. Load tables: `dim_ticker`, `fact_daily_price`, `fact_market_index`,
   `fact_market_summary`, `etl_run_log`
6. Relate `dim_ticker.ticker_id` → `fact_daily_price.ticker_id` (one-to-many)

Re-run `load_postgres.py` (or let Airflow do it on schedule) and hit
**Refresh** in Power BI to pull new numbers.

## Option B — CSV import (fastest to a working report)

```bash
cd backend
python etl/export_powerbi.py
```

Produces `powerbi/exports/stock_prices.csv`, `index_history.csv`,
`market_summary.csv`, `etl_run_log.csv`. Import each via **Get Data →
Text/CSV**.

## Suggested report layout

- **Page 1 — Market overview**: NASI value + trend line, KPI cards (shares
  traded, deals, market cap, gainers/losers count).
- **Page 2 — Stock screener**: matrix/table on `stock_prices.csv` sorted by
  `change_pct`, conditional formatting (green/red data bars), slicer on
  `sector_approx`.
- **Page 3 — Sector view**: bar chart of average `change_pct` grouped by
  `sector_approx` — which sectors moved together today.
- **Page 4 — Pipeline health**: table on `etl_run_log` — same "is the
  pipeline healthy" pattern as the cost-of-living project.

## Honest note on data completeness

Until you've run `scrape_nse.py` against the live site at least once, the
stock-level data only covers the 12 tickers that appeared in the source's
"Top Gainers / Bottom Losers" sidebar — not all ~67 listed securities. See
the root README and `backend/etl/SOURCES.md` for why, and run the scraper
for the full picture.
