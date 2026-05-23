/**
 * 骨架屏卡片组件。
 *
 * 使用 Tailwind CSS `animate-pulse` 实现脉动动画，
 * 布局与 RepoTrendingCard 对应，用于加载态占位。
 */
export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-slate-700 bg-slate-800/50 p-5">
      {/* 排名数字占位 */}
      <div className="flex items-start justify-between">
        <div className="h-8 w-8 rounded-full bg-slate-700" />
        <div className="h-5 w-16 rounded bg-slate-700" />
      </div>

      {/* 标题占位 */}
      <div className="mt-4 h-5 w-3/4 rounded bg-slate-700" />

      {/* 描述占位 */}
      <div className="mt-3 space-y-2">
        <div className="h-4 w-full rounded bg-slate-700" />
        <div className="h-4 w-5/6 rounded bg-slate-700" />
      </div>

      {/* 底部标签占位 */}
      <div className="mt-4 flex items-center gap-2">
        <div className="h-5 w-14 rounded-full bg-slate-700" />
        <div className="h-5 w-20 rounded-full bg-slate-700" />
        <div className="h-5 w-16 rounded-full bg-slate-700" />
      </div>
    </div>
  );
}

/**
 * 生成指定数量的骨架屏卡片列表。
 *
 * @param count - 骨架屏卡片数量
 */
export function SkeletonCardList({ count = 9 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}