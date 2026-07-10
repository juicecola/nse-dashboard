"""
test_scrape_nse.py
--------------------
Validates scrape_nse.py's parsing functions against the local HTML fixture
(fixtures/nse_sample_page.html) - no network access required, so this runs
anywhere, including CI.

This tests the PARSING LOGIC (does it correctly read <table> cells and
extract the index/summary numbers from prose), not whether the live site's
actual markup matches the fixture - that part still needs a real run
against afx.kwayisi.org (see SOURCES.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape_nse import parse_listings_table, parse_nasi_index, parse_daily_summary
import re

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "nse_sample_page.html"


def test_listings_table():
    html = FIXTURE.read_text()
    df = parse_listings_table(html)

    assert "ticker" in df.columns, f"Expected a 'ticker' column, got {list(df.columns)}"
    assert "EQTY" in df["ticker"].values, "Expected EQTY in parsed listings"

    eqty = df[df["ticker"] == "EQTY"].iloc[0]
    assert float(eqty["close_price"]) == 67.00, f"Expected EQTY price 67.00, got {eqty['close_price']}"
    assert int(eqty["volume"]) == 32885, f"Expected EQTY volume 32885, got {eqty['volume']}"

    cgen = df[df["ticker"] == "CGEN"].iloc[0]
    assert float(cgen["close_price"]) == 56.00, f"Expected CGEN price 56.00 (sidebar-verified), got {cgen['close_price']}"

    print(f"PASS test_listings_table: {len(df)} rows parsed, EQTY and CGEN values correct")


def test_nasi_index():
    html = FIXTURE.read_text()
    text = re.sub(r"\s+", " ", html)
    result = parse_nasi_index(text)

    assert result["close_value"] == 186.58, f"Expected NASI 186.58, got {result['close_value']}"
    assert result["ytd_pct"] == 51.1, f"Expected YTD 51.1%, got {result['ytd_pct']}"

    print(f"PASS test_nasi_index: {result}")


def test_daily_summary():
    html = FIXTURE.read_text()
    text = re.sub(r"\s+", " ", html)
    result = parse_daily_summary(text)

    assert result["total_shares_traded"] == 11070247, f"Expected 11070247 shares, got {result['total_shares_traded']}"
    assert result["total_deals"] == 4531, f"Expected 4531 deals, got {result['total_deals']}"
    assert result["gainers_count"] == 33, f"Expected 33 gainers, got {result['gainers_count']}"
    assert result["losers_count"] == 17, f"Expected 17 losers, got {result['losers_count']}"

    print(f"PASS test_daily_summary: {result}")


if __name__ == "__main__":
    test_listings_table()
    test_nasi_index()
    test_daily_summary()
    print("\nAll parsing tests passed against the local fixture.")
    print("Next step: run `python scrape_nse.py --dry-run` against the LIVE site to confirm the real markup matches.")
