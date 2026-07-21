import Ticker from "./components/Ticker";
import IndexHero from "./components/IndexHero";
import MarketSummaryCards from "./components/MarketSummaryCards";
import GainersLosersPanel from "./components/GainersLosersPanel";
import StockTable from "./components/StockTable";
import Methodology from "./components/Methodology";
import LastUpdated from "./components/LastUpdated";
import DashboardSkeleton from "./components/DashboardSkeleton";
import TopMovers from "./components/TopMovers";
import SectorBreakdown from "./components/SectorBreakdown";
import EtlHealth from "./components/EtlHealth";
import { useDashboardData } from "./hooks/useDashboardData";
export default function App() {
  const { stocks, indexHistory, summary, gainersLosers, loading, error } = useDashboardData();
  if (error) {
    return (
      <div className="h-screen flex items-center justify-center flex-col gap-3 text-center px-6">
        <div className="font-display text-2xl text-loss">Couldn't reach the API</div>
        <p className="text-muted text-sm max-w-md">
          {error}. Make sure the backend is running at the URL in{" "}
          <code className="text-gold">VITE_API_BASE</code> (default{" "}
          <code className="text-gold">http://localhost:8000</code>) — see the README for setup steps.
        </p>
      </div>
    );
  }
  if (loading) {
    return <DashboardSkeleton />;
  }
  return (
    <div className="min-h-screen flex flex-col">
      <Ticker summary={summary} index={indexHistory[indexHistory.length - 1] ?? null} />
      <header className="px-6 md:px-10 pt-10 pb-6 border-b border-line">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <div className="text-[11px] tracking-[0.2em] text-gold font-mono">
              NAIROBI SECURITIES EXCHANGE · MARKET DASHBOARD
            </div>
            <LastUpdated stocks={stocks} indexHistory={indexHistory} />
          </div>
          <h1 className="font-display text-4xl md:text-5xl text-paper leading-tight max-w-3xl">
            What did the NSE actually do today?
          </h1>
          <p className="text-muted mt-4 max-w-2xl leading-relaxed">
            NASI index, daily gainers &amp; losers, and full-listing prices for the Nairobi Securities
            Exchange — scraped from a public market data source, orchestrated by Airflow, and stored in
            Postgres as a real accumulating time series.
          </p>
        </div>
      </header>
      <main className="flex-1 px-6 md:px-10 py-8">
        <div className="max-w-6xl mx-auto flex flex-col gap-6">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.6fr] gap-6">
            <IndexHero history={indexHistory} />
            <MarketSummaryCards summary={summary} />
          </div>
          <TopMovers gainers={gainersLosers?.gainers ?? []} losers={gainersLosers?.losers ?? []} />
          <GainersLosersPanel gainers={gainersLosers?.gainers ?? []} losers={gainersLosers?.losers ?? []} />
          <SectorBreakdown stocks={stocks} />
          <StockTable data={stocks} />
          <Methodology />
          <EtlHealth />
        </div>
      </main>
      <footer className="px-6 md:px-10 py-6 border-t border-line text-center">
        <span className="text-[11px] text-muted font-mono">
          Data: afx.kwayisi.org (community NSE aggregator) — refreshed via{" "}
          <code className="text-gold">backend/etl/scrape_nse.py</code> + Airflow
        </span>
      </footer>
    </div>
  );
}
