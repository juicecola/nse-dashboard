import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Stock, IndexPoint, MarketSummary, GainersLosers } from "../lib/types";

interface DashboardData {
  stocks: Stock[];
  indexHistory: IndexPoint[];
  summary: MarketSummary | null;
  gainersLosers: GainersLosers | null;
  loading: boolean;
  error: string | null;
}

export function useDashboardData(): DashboardData {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [indexHistory, setIndexHistory] = useState<IndexPoint[]>([]);
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [gainersLosers, setGainersLosers] = useState<GainersLosers | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, ih, sm, gl] = await Promise.all([
          api.stocks(),
          api.indexHistory(),
          api.marketSummary(),
          api.gainersLosers(),
        ]);
        if (cancelled) return;
        setStocks(s);
        setIndexHistory(ih);
        setSummary(sm);
        setGainersLosers(gl);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { stocks, indexHistory, summary, gainersLosers, loading, error };
}
