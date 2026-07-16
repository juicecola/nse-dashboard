import { useEffect, useState } from "react";

const SLOW_LOAD_THRESHOLD_MS = 4000;

export default function LoadingScreen() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_LOAD_THRESHOLD_MS);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="h-screen flex items-center justify-center flex-col gap-4 text-center px-6">
      <div className="flex items-center gap-3">
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold opacity-60" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-gold" />
        </span>
        <span className="font-mono text-xs tracking-[0.2em] text-gold">
          NAIROBI SECURITIES EXCHANGE
        </span>
      </div>

      <div className="font-display text-2xl text-paper">
        {slow ? "Waking up the server…" : "Loading market data…"}
      </div>

      <p className="text-muted text-sm max-w-sm leading-relaxed">
        {slow
          ? "The backend is hosted on Render's free tier, which spins down when idle. First load after a quiet period can take up to a minute — hang tight, it's on its way."
          : "Fetching the latest NASI index, listings, and gainers & losers."}
      </p>
    </div>
  );
}
