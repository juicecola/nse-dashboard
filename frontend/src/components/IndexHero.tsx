import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import type { IndexPoint } from "../lib/types";

export default function IndexHero({ history }: { history: IndexPoint[] }) {
  const latest = history[history.length - 1];
  if (!latest) {
    return (
      <div className="border border-line rounded-lg bg-surface p-6 animate-pulse h-40" />
    );
  }

  const isUp = (latest.change_pct ?? 0) >= 0;

  return (
    <div className="border border-line rounded-lg bg-surface p-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] tracking-widest text-muted font-mono mb-2">
            NASI · NSE ALL-SHARE INDEX
          </div>
          <div className="flex items-baseline gap-3">
            <span className="font-display text-5xl text-paper">
              {latest.close_value != null ? latest.close_value.toFixed(2) : "—"}
            </span>
            {latest.change_pct !== null && (
              <span
                className={`font-mono text-lg font-semibold ${isUp ? "text-gain" : "text-loss"}`}
              >
                {isUp ? "▲" : "▼"} {Math.abs(latest.change_pct).toFixed(2)}%
              </span>
            )}
          </div>
          {latest.ytd_pct !== null && (
            <div className="text-muted text-sm font-mono mt-1">
              YTD {latest.ytd_pct >= 0 ? "+" : ""}
              {latest.ytd_pct}%
            </div>
          )}
          {(latest.week_1_pct !== null || latest.week_4_pct !== null) && (
            <div className="flex gap-4 text-muted text-xs font-mono mt-1">
              {latest.week_1_pct !== null && (
                <span>
                  1W{" "}
                  <span className={latest.week_1_pct >= 0 ? "text-gain" : "text-loss"}>
                    {latest.week_1_pct >= 0 ? "+" : ""}
                    {latest.week_1_pct}%
                  </span>
                </span>
              )}
              {latest.week_4_pct !== null && (
                <span>
                  4W{" "}
                  <span className={latest.week_4_pct >= 0 ? "text-gain" : "text-loss"}>
                    {latest.week_4_pct >= 0 ? "+" : ""}
                    {latest.week_4_pct}%
                  </span>
                </span>
              )}
            </div>
          )}
          <div className="text-muted text-xs font-mono mt-3">
            As of {latest.trade_date}
          </div>
        </div>

        {history.length > 1 && (
          <div className="w-40 h-20">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <YAxis domain={["dataMin - 5", "dataMax + 5"]} hide />
                <Line
                  type="monotone"
                  dataKey="close_value"
                  stroke={isUp ? "#3FBF7F" : "#E0654F"}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {history.length <= 2 && (
        <div className="mt-4 text-xs text-muted bg-ink/60 border border-line rounded px-3 py-2">
          Only {history.length} data point{history.length === 1 ? "" : "s"} so far — this series
          fills in as the scraper runs daily. See "Methodology" below.
        </div>
      )}
    </div>
  );
}
