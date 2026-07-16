function Block({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-surface border border-line rounded-lg ${className}`} />;
}

export default function DashboardSkeleton() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="h-9 border-b border-line bg-surface animate-pulse" />

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
