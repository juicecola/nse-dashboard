import type { MarketSummary } from "../lib/types";

export default function MarketSummaryCards({ summary }: { summary: MarketSummary | null }) {
  if (!summary) return null;

  const cards = [
    { label: "SHARES TRADED", value: summary.total_shares_traded?.toLocaleString() ?? "—" },
    { label: "DEALS", value: summary.total_deals?.toLocaleString() ?? "—" },
    {
      label: "MARKET VALUE (KES)",
      value: summary.market_value_kes ? (summary.market_value_kes / 1_000_000).toFixed(1) + "M" : "—",
    },
    {
      label: "MARKET CAP (KES)",
      value: summary.market_cap_kes ? (summary.market_cap_kes / 1_000_000_000_000).toFixed(2) + "Tr" : "—",
    },
    {
      label: "GAINERS / LOSERS",
      value: `${summary.gainers_count ?? "—"} / ${summary.losers_count ?? "—"}`,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="border border-line rounded-lg bg-surface p-4">
          <div className="text-[10px] tracking-widest text-muted font-mono mb-1">{c.label}</div>
          <div className="font-mono text-lg text-paper">{c.value}</div>
        </div>
      ))}
    </div>
  );
}
