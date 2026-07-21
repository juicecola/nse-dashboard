import { useMemo } from "react";
import type { Stock } from "../lib/types";

interface SectorStat {
  sector: string;
  avgChangePct: number;
  count: number;
}

export default function SectorBreakdown({ stocks }: { stocks: Stock[] }) {
  const sectors = useMemo<SectorStat[]>(() => {
    const groups = new Map<string, number[]>();
    for (const s of stocks) {
      if (s.change_pct == null) continue;
      const key = s.sector_approx ?? "Unclassified";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(s.change_pct);
    }
    return Array.from(groups.entries())
      .map(([sector, changes]) => ({
        sector,
        avgChangePct: changes.reduce((a, b) => a + b, 0) / changes.length,
        count: changes.length,
      }))
      .sort((a, b) => b.avgChangePct - a.avgChangePct);
  }, [stocks]);

  if (sectors.length === 0) return null;

  const maxAbs = Math.max(...sectors.map((s) => Math.abs(s.avgChangePct)), 1);

  return (
    <div className="border border-line rounded-lg bg-surface p-5">
      <div className="text-[11px] tracking-widest text-muted font-mono mb-4">
        SECTOR PERFORMANCE · AVG CHANGE %
      </div>
      <div className="flex flex-col gap-2.5">
        {sectors.map((s) => {
          const isUp = s.avgChangePct >= 0;
          const widthPct = (Math.abs(s.avgChangePct) / maxAbs) * 100;
          return (
            <div key={s.sector} className="flex items-center gap-3">
              <div className="w-32 shrink-0 text-xs text-muted truncate" title={s.sector}>
                {s.sector}
              </div>
              <div className="flex-1 h-4 bg-ink rounded overflow-hidden relative flex items-center">
                <div
                  className={`h-full ${isUp ? "bg-gain" : "bg-loss"} opacity-70`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
              <div className={`w-16 shrink-0 text-right font-mono text-xs font-semibold ${isUp ? "text-gain" : "text-loss"}`}>
                {isUp ? "+" : ""}
                {s.avgChangePct.toFixed(2)}%
              </div>
              <div className="w-8 shrink-0 text-right text-[10px] text-muted font-mono">{s.count}</div>
            </div>
          );
        })}
      </div>
      <div className="text-[10px] text-muted mt-3 font-mono">
        Averaged from same-day change % across listed tickers per sector. "Unclassified" covers tickers
        without a mapped sector in dim_ticker.
      </div>
    </div>
  );
}
