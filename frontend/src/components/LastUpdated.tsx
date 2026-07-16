import type { Stock, IndexPoint } from "../lib/types";

function mostRecentDate(stocks: Stock[], indexHistory: IndexPoint[]): string | null {
  const dates = [
    ...stocks.map((s) => s.trade_date),
    ...indexHistory.map((p) => p.trade_date),
  ].filter(Boolean);
  if (dates.length === 0) return null;
  return dates.reduce((latest, d) => (d > latest ? d : latest));
}

function daysAgo(dateStr: string): number {
  const today = new Date();
  const then = new Date(dateStr);
  const diffMs = today.setHours(0, 0, 0, 0) - then.setHours(0, 0, 0, 0);
  return Math.round(diffMs / (1000 * 60 * 60 * 24));
}

export default function LastUpdated({
  stocks,
  indexHistory,
}: {
  stocks: Stock[];
  indexHistory: IndexPoint[];
}) {
  const latest = mostRecentDate(stocks, indexHistory);
  if (!latest) return null;

  const age = daysAgo(latest);
  // > 3 days stale is worth flagging - a normal weekend/holiday gap is 1-3 days.
  const stale = age > 3;

  return (
    <div
      className={`text-[10px] font-mono tracking-wide px-2 py-1 rounded border ${
        stale ? "border-loss text-loss" : "border-line text-muted"
      }`}
      title={`Most recent trading data: ${latest}`}
    >
      {stale ? "⚠ " : ""}
      DATA AS OF {latest}
      {age > 0 ? ` (${age}d ago)` : ""}
    </div>
  );
}
