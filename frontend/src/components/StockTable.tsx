import { useState, useMemo, useEffect, Fragment } from "react";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import type { Stock, StockDetail } from "../lib/types";
import { api } from "../lib/api";

type SortKey = "ticker" | "close_price" | "change_pct" | "volume" | "sector_approx";

function StockHistoryRow({ ticker, colSpan }: { ticker: string; colSpan: number }) {
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .stockDetail(ticker)
      .then((d) => !cancelled && setDetail(d))
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return (
    <tr className="border-t border-line bg-ink/40">
      <td colSpan={colSpan} className="px-3 py-3">
        {loading && <div className="text-muted text-xs font-mono">Loading price history…</div>}
        {error && <div className="text-loss text-xs font-mono">Couldn't load history for {ticker}.</div>}
        {detail && detail.history.length <= 1 && (
          <div className="text-muted text-xs font-mono">
            Only {detail.history.length} day{detail.history.length === 1 ? "" : "s"} of history so far for{" "}
            {ticker} — this fills in as the scraper accumulates more daily loads.
          </div>
        )}
        {detail && detail.history.length > 1 && (
          <div className="flex items-center gap-4">
            <div className="w-48 h-16 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={detail.history}>
                  <YAxis domain={["dataMin - 1", "dataMax + 1"]} hide />
                  <Line
                    type="monotone"
                    dataKey="close_price"
                    stroke="#C9A24B"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="text-xs text-muted font-mono">
              {detail.history.length} trading day{detail.history.length === 1 ? "" : "s"} of history ·{" "}
              {detail.history[0].trade_date} → {detail.history[detail.history.length - 1].trade_date}
            </div>
          </div>
        )}
      </td>
    </tr>
  );
}

export default function StockTable({ data }: { data: Stock[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("change_pct");
  const [asc, setAsc] = useState(false);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = useMemo(
    () =>
      data.filter(
        (s) =>
          s.ticker.toLowerCase().includes(filter.toLowerCase()) ||
          s.name.toLowerCase().includes(filter.toLowerCase())
      ),
    [data, filter]
  );

  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" && typeof bv === "string") {
        return asc ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return asc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return copy;
  }, [filtered, sortKey, asc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(false);
    }
  }

  function toggleExpand(ticker: string) {
    setExpanded(expanded === ticker ? null : ticker);
  }

  const Th = ({ label, k }: { label: string; k: SortKey }) => (
    <th
      onClick={() => toggleSort(k)}
      className="text-left text-[10px] tracking-widest text-muted font-mono px-3 py-2 cursor-pointer select-none hover:text-gold whitespace-nowrap"
    >
      {label.toUpperCase()} {sortKey === k ? (asc ? "↑" : "↓") : ""}
    </th>
  );

  return (
    <div className="border border-line rounded-lg bg-surface overflow-hidden">
      <div className="p-3 border-b border-line">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by ticker or company name…"
          className="w-full bg-ink border border-line rounded px-3 py-2 text-sm text-paper placeholder:text-muted font-mono focus:outline-none focus:border-gold"
        />
      </div>
      <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface-raised z-10">
            <tr>
              <Th label="Ticker" k="ticker" />
              <Th label="Sector" k="sector_approx" />
              <Th label="Price (KES)" k="close_price" />
              <Th label="Change" k="change_pct" />
              <Th label="Volume" k="volume" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => {
              const isUp = (s.change_pct ?? 0) >= 0;
              const isExpanded = expanded === s.ticker;
              return (
                <Fragment key={s.ticker}>
                  <tr
                    onClick={() => toggleExpand(s.ticker)}
                    className="border-t border-line hover:bg-surface-raised transition-colors cursor-pointer"
                  >
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-muted text-[10px]">{isExpanded ? "▾" : "▸"}</span>
                        <div>
                          <div className="font-mono font-semibold text-paper">{s.ticker}</div>
                          <div className="text-muted text-xs">{s.name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-muted text-xs">{s.sector_approx ?? "—"}</td>
                    <td className="px-3 py-2 font-mono text-paper">
                      {s.close_price !== null ? s.close_price.toFixed(2) : "—"}
                    </td>
                    <td className={`px-3 py-2 font-mono font-semibold ${s.change_pct != null ? (isUp ? "text-gain" : "text-loss") : "text-muted"}`}>
                      {s.change_pct !== null ? `${isUp ? "+" : ""}${s.change_pct.toFixed(2)}%` : "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-muted">
                      {s.volume !== null ? s.volume.toLocaleString() : "—"}
                    </td>
                  </tr>
                  {isExpanded && <StockHistoryRow ticker={s.ticker} colSpan={5} />}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
