/** Suspense fallback 骨架屏组件 */
export function LazyFallback() {
  return (
    <div className="mx-auto max-w-7xl animate-pulse px-4 py-6">
      {/* 标题骨架 */}
      <div className="mb-6">
        <div className="h-8 w-64 rounded-lg bg-slate-700/50" />
        <div className="mt-2 h-4 w-96 rounded bg-slate-700/30" />
      </div>

      {/* 卡片骨架 */}
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-5"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="h-5 w-48 rounded bg-slate-700/50" />
                <div className="mt-2 h-4 w-full max-w-md rounded bg-slate-700/30" />
                <div className="mt-3 flex gap-3">
                  <div className="h-4 w-16 rounded bg-slate-700/40" />
                  <div className="h-4 w-12 rounded bg-slate-700/40" />
                  <div className="h-4 w-20 rounded bg-slate-700/40" />
                </div>
              </div>
              <div className="h-8 w-8 rounded-lg bg-slate-700/40" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
