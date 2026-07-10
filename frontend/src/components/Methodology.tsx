export default function Methodology() {
  return (
    <div className="border border-line rounded-lg bg-surface p-6">
      <h3 className="font-display text-xl text-paper mb-4">Methodology &amp; data honesty</h3>

      <div className="space-y-4 text-sm text-muted leading-relaxed">
        <p>
          <span className="text-paper font-medium">There is no official free NSE API.</span> This
          dashboard scrapes a public, community-run market data aggregator
          (<span className="text-gold">afx.kwayisi.org</span>), not an official NSE or CMA feed. Paid
          alternatives exist (Mansa Markets, ICE Data Services) if you need guaranteed uptime and SLAs.
        </p>
        <p>
          <span className="text-paper font-medium">What's shipped as real vs. a placeholder:</span> the
          67-ticker name/sector mapping and the NASI index history are real, dated, sourced data. The
          full daily price/volume table for all 67 tickers is <em>not</em> pre-seeded — the raw page text
          concatenated table columns without reliable delimiters (e.g. is "CGEN...756.00+5.00" a volume of
          75 and price of 6.00, or something else?), and rather than guess and risk shipping wrong numbers
          labeled as real, that table is left for the scraper to populate from actual HTML table cells,
          where column boundaries aren't ambiguous. What you're looking at right now, before you've run
          the scraper yourself, is the partial "Top Gainers / Bottom Losers" sidebar data (12 tickers)
          that <em>was</em> unambiguous in the source text.
        </p>
        <p>
          <span className="text-paper font-medium">Run the scraper to get the full picture:</span>{" "}
          <code className="text-gold">python backend/etl/scrape_nse.py</code> pulls the live page and
          populates all ~67 tickers with real volume/price/change data via proper table parsing. It was
          validated against a local HTML fixture (<code className="text-gold">test_scrape_nse.py</code>,
          all tests passing) but not against the live site itself, since the environment that built this
          project has network access restricted to package registries only — that's the first thing to
          verify once you run it from your own machine.
        </p>
        <p>
          <span className="text-paper font-medium">This is a genuinely time-series dataset:</span> unlike
          a slow-moving census figure, the NSE closes daily and this page's numbers are only ever one
          trading day old. Scheduling the scraper (via the included Airflow DAG, weekdays after market
          close) is what turns this from a single snapshot into a real historical series worth charting.
        </p>
      </div>
    </div>
  );
}
