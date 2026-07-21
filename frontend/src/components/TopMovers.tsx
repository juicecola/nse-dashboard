import type { Stock } from "../lib/types";

function MoverCard({ label, stock, isGain }: { label: string; stock: Stock; isGain: boolean }) {
  return (
    <div className="border border-line rounded-lg bg-surface p-4 flex items-center justify-between">
      <div>
        <div className={`text-[10px] tracking-widest font-mono mb-1 ${isGain ? "text-gain" : "text-loss"}`}>
          {isGain ? "▲ " : "▼ "}
          {label}
        </div>
        <div className="font-mono font-semibold text-paper">{stock.ticker}</div>
        <div className="text-muted text-xs">{stock.name}</div>
      </div>
      <div className={`font-mono text-2xl font-semibold ${isGain ? "text-gain" : "text-loss"}`}>
        {isGain ? "+" : ""}
        {stock.change_pct?.toFixed(2)}%
      </div>
    </div>
  );
}

export default function TopMovers({ gainers, losers }: { gainers: Stock[]; losers: Stock[] }) {
  const best = gainers[0];
  const worst = losers[0];

  if (!best && !worst) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {best && <MoverCard label="BEST MOVER TODAY" stock={best} isGain />}
      {worst && <MoverCard label="WORST MOVER TODAY" stock={worst} isGain={false} />}
    </div>
  );
}
