import type { Stock } from "../lib/types";

function StockRow({ s }: { s: Stock }) {
  const isUp = (s.change_pct ?? 0) >= 0;
  return (
    <div className="flex items-center justify-between py-2 border-b border-line last:border-0">
      <div>
        <span className="font-mono font-semibold text-paper">{s.ticker}</span>
        <span className="text-muted text-xs ml-2">{s.name}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-mono text-sm text-paper">KES {s.close_price?.toFixed(2)}</span>
        <span className={`font-mono text-sm font-semibold w-16 text-right ${isUp ? "text-gain" : "text-loss"}`}>
          {isUp ? "+" : ""}
          {s.change_pct?.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}

export default function GainersLosersPanel({
  gainers,
  losers,
}: {
  gainers: Stock[];
  losers: Stock[];
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="border border-line rounded-lg bg-surface p-5">
        <div className="text-[11px] tracking-widest text-gain font-mono mb-3">▲ TOP GAINERS</div>
        {gainers.length === 0 && <div className="text-muted text-sm">No gainers in the latest data.</div>}
        {gainers.map((s) => (
          <StockRow key={s.ticker} s={s} />
        ))}
      </div>
      <div className="border border-line rounded-lg bg-surface p-5">
        <div className="text-[11px] tracking-widest text-loss font-mono mb-3">▼ TOP LOSERS</div>
        {losers.length === 0 && <div className="text-muted text-sm">No losers in the latest data.</div>}
        {losers.map((s) => (
          <StockRow key={s.ticker} s={s} />
        ))}
      </div>
    </div>
  );
}
