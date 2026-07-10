# Data sources & honesty notes

## The one thing to read before anything else

**I could not run the live scraper against afx.kwayisi.org from my build
sandbox.** Its outbound network is locked to package registries only
(PyPI, npm, GitHub, apt) - a direct request to the NSE data source returned:

```
HTTP/2 403
x-deny-reason: host_not_allowed
```

That's a sandbox restriction, not a problem with the scraper or the site.
**The first thing you should do after unzipping this is run
`python etl/scrape_nse.py` yourself** (see main README) to confirm it works
against the live page from your own machine, before trusting it in Airflow.
I built it against the real page's structure (verified via a fetch on
2026-07-05, transcript below) and tested the parsing logic against a local
HTML fixture, but "tested against a fixture" is not the same as "confirmed
against the live site," and I want that distinction to be explicit rather
than implied away.

## What's real vs. what's a fixture vs. what's approximate

| Dataset | File | Status |
|---|---|---|
| Ticker → company name mapping (67 companies) | `data/dim_ticker.csv` | **Real.** Transcribed directly from the source's listings table on 2026-07-05. Names are unambiguous text, unlike the price columns (see caveat below). |
| Sector tags | `data/dim_ticker.csv` (`sector_approx` column) | **My categorization**, based on general knowledge of NSE market segments, not scraped from an official per-ticker sector feed. Column is named `sector_approx` deliberately - verify against NSE's official sector classification before treating it as authoritative. |
| NASI index history (3 points) | `data/nasi_index_seed.csv` | **Real, dated, sourced.** Each row cites the exact page it came from. This is a genuinely sparse series (3 points across ~6 months) precisely because I only have what came up in live searches during this conversation - the scraper is what turns this into a real daily series going forward. |
| Top gainers / bottom losers (12 tickers) | `data/nse_gainers_losers_seed.csv` | **Real**, for 2025-12-31. Taken from the source's "Top Gainers" / "Bottom Losers" sidebar, which uses a clean `TICKER + PRICE + %CHANGE` format that parses unambiguously. |
| Full 67-ticker daily volume/price/change table | *Not seeded* | **Deliberately not fabricated.** The raw text I got back from fetching the page concatenated table columns without reliable delimiters (e.g. `CGENCar and General Kenya Limited756.00+5.00` - is that volume 75, price 6.00? Or volume 7, price 56.00, matching the 56.00 price shown elsewhere on the same page for CGEN?). Rather than guess and risk shipping wrong numbers labeled as real, this table is left for the scraper to populate from the actual HTML `<table>` cells, where column boundaries aren't ambiguous. |
| Daily market summary (shares traded, deals, market value, market cap) | `data/nse_daily_summary_seed.csv` | **Real**, for 2025-12-31, taken from the source's own prose trading-summary paragraph (unambiguous, since these are stated as whole sentences, not concatenated table cells). Market cap is stated in the source as "KES 2.94 trillion" and stored here as the rounded figure `2,940,000,000,000` - treat the last few digits as illustrative, not exact. |

## Source

All of the above: [afx.kwayisi.org/nse](https://afx.kwayisi.org/nse/) - a
community-run African stock exchange data aggregator, not an official NSE
or CMA product. There is no official free NSE API; paid alternatives exist
(Mansa Markets offers a REST API refreshing every 30 minutes during trading
hours; ICE Data Services offers institutional-grade feeds) - see the main
README for how to swap either in if you want a cleaner data path later.

## Why the scraper design is defensible even though it's untested end-to-end

`etl/scrape_nse.py` uses `pandas.read_html()` against the live page, which
parses actual `<table>` markup (real `<td>` cell boundaries) rather than
extracted/flattened text - so the column-concatenation problem described
above shouldn't occur when it runs against the real HTML. I validated the
parsing and cleaning logic (`etl/test_scrape_nse.py`) against a saved local
fixture (`etl/fixtures/nse_sample_page.html`) built to match the real
table's column structure. What I have **not** been able to verify is that
`afx.kwayisi.org`'s actual markup matches my fixture's assumptions exactly
(table id/class, whether there are merged header rows, etc.) - that's the
first thing to check if the scraper errors out for you.
