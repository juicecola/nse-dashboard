export interface Stock {
  ticker: string;
  name: string;
  sector_approx: string | null;
  trade_date: string;
  volume: number | null;
  close_price: number | null;
  change_abs: number | null;
  change_pct: number | null;
}

export interface StockDetail extends Stock {
  history: { trade_date: string; close_price: number; change_pct: number }[];
}

export interface IndexPoint {
  index_name: string;
  trade_date: string;
  close_value: number;
  change_abs: number | null;
  change_pct: number | null;
  ytd_pct: number | null;
}

export interface MarketSummary {
  trade_date: string;
  total_shares_traded: number | null;
  total_deals: number | null;
  market_value_kes: number | null;
  market_cap_kes: number | null;
  gainers_count: number | null;
  losers_count: number | null;
  listed_companies_traded: number | null;
  source_url: string | null;
}

export interface GainersLosers {
  gainers: Stock[];
  losers: Stock[];
}
