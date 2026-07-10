import type { MarketSummary, IndexPoint } from "../lib/types";

export default function Ticker({
  summary,
  index,
}: {
  summary: MarketSummary | null;
  index: IndexPoint | null;
}) {
  if (!summary || !index) {
    return (
      <div className="h-10 bg-surface border-b border-line flex items-center px-6">
        <span className="text-muted text-xs font-mono">Loading market data…</span>
      </div>
    );
  }

  const items = [
    { label: "NASI", value: `${index.close_value.toFixed(2)}` },
    { label: "CHANGE", value: `${(index.change_pct ?? 0) >= 0 ? "+" : ""}${index.change_pct?.toFixed(2) ?? "—"}%` },
    { label: "AS OF", value: summary.trade_date },
    { label: "GAINERS/LOSERS", value: `${summary.gainers_count ?? "—"}/${summary.losers_count ?? "—"}` },
    { label: "DEALS", value: `${summary.total_deals?.toLocaleString() ?? "—"}` },
    { label: "MARKET CAP", value: summary.market_cap_kes ? `KES ${(summary.market_cap_kes / 1e12).toFixed(2)}Tr` : "—" },
  ];

  const row = (prefix: string) => (
    <div className="flex items-center gap-8 shrink-0">
      {items.map((it, i) => (
        <div key={`${prefix}-${i}`} className="flex items-center gap-2 whitespace-nowrap">
          <span className="text-[10px] tracking-widest text-muted font-mono">{it.label}</span>
          <span className="text-sm font-mono font-semibold text-gold">{it.value}</span>
          <span className="text-line mx-2">/</span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="h-10 bg-surface border-b border-line overflow-hidden flex items-center">
      <div className="flex animate-ticker">
        {row("a")}
        {row("b")}
      </div>
    </div>
  );
}
