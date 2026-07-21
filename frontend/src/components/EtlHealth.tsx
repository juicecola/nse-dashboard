import { useEffect, useState } from "react";

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

interface RunLogEntry {
  run_date: string;
  task_name: string;
  rows_loaded: number;
  status: string;
  detail: string;
}

export default function EtlHealth() {
  const [entries, setEntries] = useState<RunLogEntry[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${BASE}/api/etl/run-log`)
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setEntries)
      .catch(() => setError(true));
  }, []);

  if (error || !entries || entries.length === 0) return null;

  const latestByTask = new Map<string, RunLogEntry>();
  for (const e of entries) {
    if (!latestByTask.has(e.task_name)) latestByTask.set(e.task_name, e);
  }
  const latest = Array.from(latestByTask.values());
  const mostRecentRun = entries[0];
  const allHealthy = latest.every((e) => e.status === "success");

  return (
    <details className="border border-line rounded-lg bg-surface p-4 text-xs">
      <summary className="cursor-pointer select-none flex items-center gap-2 text-muted font-mono">
        <span className={`inline-block w-2 h-2 rounded-full ${allHealthy ? "bg-gain" : "bg-loss"}`} />
        Pipeline status: {allHealthy ? "healthy" : "issues detected"} · last run {mostRecentRun.run_date}
      </summary>
      <div className="mt-3 flex flex-col gap-1.5">
        {latest.map((e) => (
          <div key={e.task_name} className="flex items-center justify-between font-mono">
            <span className="text-muted">{e.task_name}</span>
            <span className="flex items-center gap-3">
              <span className="text-muted">{e.rows_loaded} rows</span>
              <span className={e.status === "success" ? "text-gain" : "text-loss"}>{e.status}</span>
            </span>
          </div>
        ))}
      </div>
    </details>
  );
}
