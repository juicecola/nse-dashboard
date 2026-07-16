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
          <span className="text-paper font-medium">This is a time-series dataset:</span> unlike
          a slow-moving census figure, the NSE closes daily and this page's numbers are only ever one
          trading day old. Scheduling the scraper (via the included Airflow DAG, weekdays after market
          close) is what turns this from a single snapshot into a real historical series worth charting.
        </p>
      </div>
    </div>
  );
}
