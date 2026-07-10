import type { Stock, StockDetail, IndexPoint, MarketSummary, GainersLosers } from "./types";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  return res.json() as Promise<T>;
}

export const api = {
  stocks: () => getJSON<Stock[]>("/api/stocks"),
  stockDetail: (ticker: string) => getJSON<StockDetail>(`/api/stocks/${ticker}`),
  indexHistory: () => getJSON<IndexPoint[]>("/api/index/history"),
  marketSummary: () => getJSON<MarketSummary>("/api/market/summary"),
  gainersLosers: () => getJSON<GainersLosers>("/api/market/gainers-losers"),
};
