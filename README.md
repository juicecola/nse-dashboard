# NSE Kenya Market Dashboard

**What did the Nairobi Securities Exchange actually do today?**

A full-stack market dashboard for the NSE — scraped from a real, live,
publicly-updating source (there's no official free NSE API), orchestrated
with Airflow, stored in Postgres as a genuine daily time series, served by
FastAPI, visualized in React, and exportable to Power BI.

![stack](https://img.shields.io/badge/backend-FastAPI-0B1614) ![stack](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-12211E) ![stack](https://img.shields.io/badge/data-NSE%20live-E3B23C)

## Why this project

Every source in the earlier Kenya cost-of-living project updates slowly
(census once every few years, poverty estimates once a decade) — which
means a scheduler like Airflow is a nice-to-have there, not a necessity.
The NSE is different: it closes every trading day with a genuinely new set
of numbers. This project exists specifically to pair Postgres/Airflow with
a dataset where **daily scheduling is actually required**, not just
demonstrated.

## What it does

- **NASI index** hero card with trend sparkline (fills in as the scraper
  accumulates daily runs)
- **Gainers/losers panel** — top movers by % change
- **Full stock table** — all listed tickers, sortable and filterable by
  ticker/name, with an approximate sector tag
- **Market summary** — shares traded, deals, market cap, gainers/losers count
- A **"Methodology & data honesty"** panel in the app itself, disclosing
  exactly what's real scraped data vs. seed data, and why

## The honest data story (read this before a demo or interview)

There is no official free NSE API. This scrapes a public, community-run
aggregator (`afx.kwayisi.org`). The 67-ticker name/sector mapping and the
3-point NASI index history shipped in `data/` are real, dated numbers I
pulled from a live fetch. The **full daily price/volume table for all ~67
tickers is not pre-seeded** — the page's raw text concatenates table
columns without reliable delimiters (e.g., is `"75" "6.00" "+5.00"` really
volume 75 / price 6.00, or something else entirely?), and rather than guess
and ship wrong numbers labeled as real, the pre-seeded stock data is
limited to the 12 tickers that appeared unambiguously in the source's "Top
Gainers / Bottom Losers" sidebar.

**Run `python backend/etl/scrape_nse.py` against the live site to populate
the rest** — the scraper reads actual HTML `<table>` cells, where column
boundaries aren't ambiguous, so it gets all ~67 tickers correctly. It's
validated against a local HTML fixture (`backend/etl/test_scrape_nse.py` —
all 3 tests pass, including one bug the fixture caught: `pd.read_html()`
needs its input wrapped in `io.StringIO()` or it misfires) but **not yet
run against the live site itself**, since the environment used to build
this had network access restricted to package registries only. That's the
first thing to verify once you run it from your own machine.

Full source-by-source citations: [`backend/etl/SOURCES.md`](backend/etl/SOURCES.md)

## Architecture

```
afx.kwayisi.org (live NSE data, no official API)
        │
        ▼
Airflow DAG (airflow/dags/nse_pipeline.py) — weekdays, after market close
  scrape_nse → load_postgres → data_quality_checks
        → export_static_json → export_powerbi_csv
        │
        ▼
Postgres (dim_ticker, fact_daily_price, fact_market_index,
          fact_market_summary, etl_run_log)
        │
        ├──────────────┐
        ▼              ▼
FastAPI (backend/app/main.py)      Power BI
  Postgres-first, falls back          (backend/etl/export_powerbi.py,
  to static JSON snapshot             or a direct Postgres connection —
                                       see powerbi/README.md)
        │
        ▼
React + TypeScript + Tailwind (frontend/)
  Index hero, gainers/losers, sortable stock table, ticker
```

## Running it — quick mode (no Postgres/Airflow/Docker)

```bash
cd backend
pip install -r requirements.txt
python etl/build_static_export.py    # exports from CSV seeds directly
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

`/api/health` will show `"postgres": false` — expected, and the API falls
back to the static snapshot (12 seeded tickers).

## Running it — full mode (Postgres + Airflow + Docker)

```bash
docker-compose up -d
```

Then, either trigger the DAG in the Airflow UI (`http://localhost:8080`,
login `admin`/`admin`, DAG `nse_pipeline` — paused by default, unpause and
trigger manually), or run the steps directly:

```bash
docker-compose exec backend python etl/scrape_nse.py       # live scrape - needs real internet
docker-compose exec backend python etl/load_postgres.py
docker-compose exec backend python etl/build_static_export.py
docker-compose exec backend python etl/export_powerbi.py
```

Frontend runs the same way as quick mode. `/api/health` should now show
`"postgres": true` and `/api/stocks` should return close to 67 tickers
instead of 12.

## What I verified myself vs. what still needs your run

**Verified, with a real Postgres instance and real data:**
- The full Postgres schema loads correctly (`dim_ticker`, `fact_daily_price`,
  `fact_market_index`, `fact_market_summary`, `etl_run_log`) — 67 tickers,
  3-point NASI history, 12-ticker gainers/losers set, all confirmed with
  direct SQL queries.
- FastAPI serves correctly from Postgres (`"postgres": true`) and correctly
  falls back to flat files when Postgres is unreachable — both paths tested.
- The Power BI CSV export runs against live Postgres and produces correct
  files.
- The scraper's **parsing logic** passes against a local HTML fixture
  (3/3 tests), including a real bug it caught and I fixed
  (`pd.read_html()` + `StringIO`).

**Not verified — needs a real run on your machine:**
- The scraper against the *actual live site* (`afx.kwayisi.org`) — my
  sandbox's network access doesn't reach it, only package registries.
- The full `docker-compose up` orchestration end-to-end (no Docker daemon
  in my sandbox) — the Postgres schema and load scripts are verified
  against a real local Postgres instance, but the container networking
  between Postgres/Airflow/backend hasn't been run by me.

## Scheduling: Airflow vs. cron

This project ships **three ways to schedule the daily scrape** — pick one,
don't run more than one at a time, or you'll scrape/load the same day
twice.

| Option | When to use it | How |
|---|---|---|
| **Airflow DAG** | You want a UI, retry policy, and run-history table, and don't mind the overhead of a webserver+scheduler running 24/7 for one daily task | Unpause `nse_pipeline` at `localhost:8080` |
| **Host crontab** | Simplest option if you already have `docker-compose up -d` running and just want it automated with minimal moving parts | `scripts/run_pipeline.sh` + a crontab entry — see below |
| **Dockerized cron sidecar** | You're deploying to a VPS and want everything containerized, no host-level crontab dependency | `docker-compose --profile cron up -d` — see `infra/cron/` |

Being honest about the tradeoff: for a single daily task, Airflow is
genuinely more infrastructure than the job needs — its value is the UI,
retries, and audit trail, not that the task itself is complex. Cron is the
right call if you just want it running reliably with the least moving
parts; Airflow is the right call if you want to *demonstrate* orchestration
skills, or if this pipeline is likely to grow more DAGs later.

### Host crontab setup

```bash
# 1. Test it manually first
./scripts/run_pipeline.sh

# 2. Check the log
cat logs/pipeline.log

# 3. Add to your crontab (crontab -e), matching Airflow's schedule:
#    16:05 Nairobi time, weekdays (adjust for your server's timezone)
5 16 * * 1-5 cd /home/munyi/nse-dashboard && ./scripts/run_pipeline.sh >> logs/cron.log 2>&1
```

Check `crontab -l` to confirm it saved, and `date` to confirm your
machine's timezone before picking the hour — the example above assumes the
machine is already set to Africa/Nairobi (UTC+3); adjust to `5 13 * * 1-5`
if your machine's clock is UTC.

### Dockerized cron sidecar setup

```bash
docker-compose --profile cron up -d --build cron
docker-compose logs -f cron          # watch it start
docker exec -it nse-dashboard-cron-1 crontab -l   # confirm the schedule loaded
```

Logs land inside the container at `/var/log/nse_pipeline.log`; tail them
with `docker exec nse-dashboard-cron-1 tail -f /var/log/nse_pipeline.log`.

### Do you need a server for this to actually run daily?

Yes, for any of the three options — a scheduler only fires while it's
running. A laptop that sleeps/shuts down will miss runs. Cheapest reliable
path: a small VPS (Hetzner/DigitalOcean/Lightsail, ~$5-10/mo) running
`docker-compose up -d` (with either Airflow unpaused or the cron profile
started) continuously. For a portfolio piece where nobody depends on
uptime, it's also reasonable to just trigger a run manually every so often
to build up history for a demo, rather than paying for always-on hosting.

## What I'd do with more resources

- Add a paid data provider (Mansa Markets or similar) as a second scraper
  target, with a fallback chain: paid API → free scrape → seed data.
- Extend `fact_market_index` to cover NSE20, NSE25, and the banking sector
  index (the narrative text mentions these; only NASI has a clean
  structured value in the current parser).
- Add retry/backoff and a "did the page structure change" alert to
  `scrape_nse.py`, since a redesign of the source site would silently
  break the `pd.read_html()` column assumptions.
- Move to a paid intraday feed if the use case ever needs more than daily
  granularity.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, pandas, BeautifulSoup/lxml
- **Database:** PostgreSQL (`dim_ticker` + `fact_daily_price` +
  `fact_market_index` + `fact_market_summary` + `etl_run_log`)
- **Orchestration:** Apache Airflow (scrape → load → quality-check →
  export), scheduled weekdays after NSE close, via Docker Compose
- **BI:** Power BI (direct Postgres connection or CSV export)
- **Frontend:** React, TypeScript, Tailwind CSS v4, Recharts
- **Data source:** afx.kwayisi.org (public NSE data aggregator — no
  official free NSE/CMA API exists)
