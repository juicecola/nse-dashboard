import { useEffect, useState } from "react";

// Render's free tier spins the backend down after inactivity - the first
// request after that can take 30-60s to wake it back up. The skeleton
// alone still looks "stuck" through a delay that long, since nothing
// changes on screen. Surface an explanation once we're past how long a
// normal (already-warm) request takes, so a fast load stays clean but a
// cold start doesn't look broken.
const SLOW_LOAD_THRESHOLD_MS = 4000;

function Block({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-surface border border-line rounded-lg ${className}`} />;
}

export default function DashboardSkeleton() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_LOAD_THRESHOLD_MS);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <div className="h-9 border-b border-line bg-surface animate-pulse" />

      {slow && (
        <div className="px-6 md:px-10 py-2 bg-surface-raised border-b border-line">
          <div className="max-w-6xl mx-auto flex items-center gap-2">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold" />
            </span>
            <span className="text-xs text-muted">
              Waking up the server — this backend runs on Render's free tier, which spins down when
              idle. First load after a quiet period can take up to a minute.
            </span>
          </div>
        </div>
      )}

      <header className="px-6 md:px-10 pt-10 pb-6 border-b border-line">
        <div className="max-w-6xl mx-auto flex flex-col gap-3">
          <Block className="h-3 w-64" />
          <Block className="h-10 w-full max-w-xl" />
          <Block className="h-4 w-full max-w-2xl" />
        </div>
      </header>
      <main className="flex-1 px-6 md:px-10 py-8">
        <div className="max-w-6xl mx-auto flex flex-col gap-6">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.6fr] gap-6">
            <Block className="h-64" />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Block key={i} className="h-20" />
              ))}
            </div>
          </div>
          <Block className="h-40" />
          <Block className="h-80" />
        </div>
      </main>
    </div>
  );
}