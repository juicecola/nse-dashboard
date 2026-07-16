"""
scrape_nse.py
--------------
Scrapes the daily NSE trading summary from afx.kwayisi.org/nse/.

IMPORTANT - read backend/etl/SOURCES.md before trusting this in production.
This was built against the real page's structure (verified via a live fetch
on 2026-07-05) but has NOT been executed end-to-end against the live site
from the environment that built this project - that sandbox's network is
locked to package registries only. Run this yourself first:

    python etl/scrape_nse.py --dry-run

...and inspect the output before wiring it into Airflow.

WHAT IT SCRAPES
  1. The main listings table: ticker, name, volume, price, change
     -> via pandas.read_html(), which parses real <table> cell boundaries.
     This sidesteps the column-concatenation problem you get from naive
     text extraction (see SOURCES.md for a worked example of why that
     matters).
  2. The NASI index box (index value, day change, YTD change)
     -> via regex against the page text, since it's not a <table>.
  3. The daily summary paragraph (shares traded, deals, market value,
     market cap, gainers/losers count)
     -> also via regex, deliberately written defensively: every field is
     independently optional, so a change in the summary's wording degrades
     gracefully (logs a warning, leaves that field null) rather than
     crashing the whole scrape.

WHY REGEX AT ALL, GIVEN THE EARLIER WARNING ABOUT TEXT EXTRACTION: the
concatenation problem in SOURCES.md happened because *tabular* data lost
its column delimiters when flattened to text. The index box and summary
paragraph were never tabular to begin with - they're natural-language
sentences with clearly-delimited numbers (e.g. "closing at KES 0.94 per
share"), which regex handles safely. The distinction matters and is the
reason this file mixes both techniques rather than picking one.
"""

import argparse
import re
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import urllib3.util.connection as urllib3_cn

# Some GitHub Actions hosted runners resolve dual-stack hosts to an IPv6
# address but have broken/unavailable outbound IPv6 routing, which fails
# almost instantly with "OSError: [Errno 101] Network is unreachable"
# rather than timing out. Forcing IPv4 here sidesteps that entirely and
# is harmless locally, where IPv4 works fine regardless.
def _allowed_gai_family():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = _allowed_gai_family

URL = "https://afx.kwayisi.org/nse/"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (portfolio-project NSE dashboard scraper; contact: replace-with-your-email)"
}


def fetch_html(url: str = URL, attempts: int = 3) -> str:
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            print(f"Attempt {attempt}/{attempts} failed: {exc}")
            if attempt < attempts:
                wait = 5 * attempt
                print(f"Retrying in {wait}s...")
                time.sleep(wait)
    raise last_exc


def parse_listings_table(html: str) -> pd.DataFrame:
    """Parses the main ticker/name/volume/price/change table via pandas.read_html.

    NOTE: the exact table structure (column count/order, whether ticker and
    name are merged into one cell) could not be confirmed against the live
    site from the build sandbox. This function tries the most likely shape
    first and falls back to a looser parse with a warning if it doesn't
    match - check stderr output the first time you run this for real.
    """
    from io import StringIO
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError as e:
        raise RuntimeError(f"No parsable <table> found on the page - site structure may have changed: {e}")

    # Heuristic: the listings table is the largest one on the page (67 rows).
    candidate = max(tables, key=len)

    if len(candidate) < 40:
        print(f"WARNING: largest table on the page only has {len(candidate)} rows; "
              f"expected ~67 listed securities. Site structure may have changed - "
              f"inspect the raw HTML before trusting this output.", file=sys.stderr)

    # Best-effort column normalization - real column headers may differ from
    # this guess; adjust after your first real run.
    candidate.columns = [str(c).strip().lower() for c in candidate.columns]
    rename_map = {}
    for col in candidate.columns:
        if "ticker" in col or col == "symbol":
            rename_map[col] = "ticker"
        elif "name" in col or "company" in col:
            rename_map[col] = "name"
        elif "vol" in col:
            rename_map[col] = "volume"
        elif "price" in col or "close" in col or "last" in col:
            rename_map[col] = "close_price"
        elif "change" in col or "chg" in col:
            rename_map[col] = "change_abs"
    candidate = candidate.rename(columns=rename_map)

    keep = [c for c in ["ticker", "name", "volume", "close_price", "change_abs"] if c in candidate.columns]
    if "ticker" not in keep:
        raise RuntimeError(
            "Could not find a 'ticker' column after normalization. "
            f"Columns found: {list(candidate.columns)}. The site's table structure "
            "has likely changed since this scraper was written - inspect the raw "
            "HTML and update the column-matching logic above."
        )
    result = candidate[keep].copy()

    # The source table only publishes absolute change (e.g. "+0.20"), not a
    # percentage - derive it from close_price and change_abs so downstream
    # consumers (gainers/losers ranking, the frontend) have both. Guarded
    # against previous_close being zero/NaN (illiquid or newly-listed
    # counters can have odd values here).
    if "close_price" in result.columns and "change_abs" in result.columns:
        close = pd.to_numeric(result["close_price"], errors="coerce")
        change = pd.to_numeric(result["change_abs"], errors="coerce")
        previous_close = close - change
        pct = (change / previous_close) * 100
        pct = pct.replace([float("inf"), float("-inf")], pd.NA)
        result["change_pct"] = pct.where(previous_close.notna() & (previous_close != 0)).round(2)
    else:
        result["change_pct"] = None

    return result


def parse_nasi_index(text: str) -> dict:
    """Extracts the NASI index box: current value, absolute change, YTD %."""
    result = {"index_name": "NASI", "close_value": None, "change_abs": None,
              "change_pct": None, "ytd_pct": None}

    m = re.search(r"NASI\D{0,20}?([\d,]+\.\d+)\s*\(?\+?(-?[\d.]+)\)?", text)
    if m:
        result["close_value"] = float(m.group(1).replace(",", ""))
        result["change_abs"] = float(m.group(2))
    else:
        print("WARNING: could not parse NASI index box - regex may need updating for the live page.",
              file=sys.stderr)

    m = re.search(r"year-to-date gain of ([\d.]+)%", text, re.IGNORECASE)
    if m:
        result["ytd_pct"] = float(m.group(1))

    m = re.search(r"NASI\).*?moved (?:up|down) [\d.]+ \(([\-\d.]+)%\)", text)
    if m:
        result["change_pct"] = float(m.group(1))

    return result


def parse_daily_summary(text: str) -> dict:
    """Extracts the market-wide daily summary paragraph. Every field is
    independently optional - a missing field logs a warning but doesn't
    fail the whole scrape."""
    result = {
        "total_shares_traded": None, "total_deals": None, "market_value_kes": None,
        "market_cap_kes": None, "gainers_count": None, "losers_count": None,
        "listed_companies_traded": None,
    }

    m = re.search(r"total of ([\d,]+) shares in ([\d,]+) deals.*?KES ([\d,]+\.\d+)", text)
    if m:
        result["total_shares_traded"] = int(m.group(1).replace(",", ""))
        result["total_deals"] = int(m.group(2).replace(",", ""))
        result["market_value_kes"] = float(m.group(3).replace(",", ""))
    else:
        print("WARNING: could not parse shares/deals/market value sentence.", file=sys.stderr)

    m = re.search(r"market capitalization.*?is KES ([\d.]+) trillion", text, re.IGNORECASE)
    if m:
        result["market_cap_kes"] = float(m.group(1)) * 1_000_000_000_000

    m = re.search(r"(\d+) NSE listed equities participated.*?with (\d+) gainers and (\d+) losers", text)
    if m:
        result["listed_companies_traded"] = int(m.group(1))
        result["gainers_count"] = int(m.group(2))
        result["losers_count"] = int(m.group(3))
    else:
        print("WARNING: could not parse gainers/losers sentence.", file=sys.stderr)

    return result


def run(dry_run: bool = False):
    print(f"Fetching {URL} ...")
    html = fetch_html()
    text = re.sub(r"\s+", " ", html)  # loose text version for regex passes

    listings = parse_listings_table(html)
    nasi = parse_nasi_index(text)
    summary = parse_daily_summary(text)

    today = datetime.now().strftime("%Y-%m-%d")

    if dry_run:
        print("\n--- DRY RUN: nothing written ---")
        print(f"Listings parsed: {len(listings)} rows")
        print(listings.head(10))
        print(f"\nNASI: {nasi}")
        print(f"\nDaily summary: {summary}")
        return

    out_dir = DATA_DIR / "scraped"
    out_dir.mkdir(exist_ok=True)
    listings.to_csv(out_dir / f"listings_{today}.csv", index=False)
    pd.DataFrame([{**nasi, "trade_date": today}]).to_csv(out_dir / f"nasi_{today}.csv", index=False)
    pd.DataFrame([{**summary, "trade_date": today}]).to_csv(out_dir / f"summary_{today}.csv", index=False)
    print(f"Wrote scraped data for {today} to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Print parsed output without writing files - run this first.")
    args = parser.parse_args()
    run(dry_run=args.dry_run)