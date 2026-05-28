import { useMemo, useState, useRef, useCallback, useEffect } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { Repo } from "../types";
import { RepoTrendingCard } from "./RepoTrendingCard";
import { SkeletonCardList } from "./SkeletonCard";

/** 饼图配色 */
const COLORS = [
  "#6366f1", // primary-500
  "#22d3ee", // cyan
  "#f59e0b", // amber
  "#10b981", // emerald
  "#f472b6", // pink
  "#8b5cf6", // violet
  "#14b8a6", // teal
  "#f97316", // orange
];

/** TrendingList 组件属性 */
interface TrendingListProps {
  /** 项目列表 */
  repos: Repo[];
  /** 是否加载中 */
  loading: boolean;
  /** 错误信息（非空时展示错误态） */
  error: string | null;
  /** 重试回调 */
  onRetry?: () => void;
  /** 上拉加载更多回调 */
  onLoadMore?: () => void;
  /** 是否有更多数据 */
  hasMore?: boolean;
  /** 加载更多中 */
  loadingMore?: boolean;
}

/**
 * 从仓库列表聚合语言分布数据。
 */
function aggregateLanguages(repos: Repo[]) {
  const counts: Record<string, number> = {};
  for (const repo of repos) {
    const lang = repo.language || "Other";
    counts[lang] = (counts[lang] || 0) + 1;
  }
  return Object.entries(counts)
    .map(([language, count]) => ({ language, count }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Trending 项目列表组件。
 *
 * 支持四种状态：loading / error / empty / 正常
 * 支持移动端下拉刷新 + 上拉加载更多
 * 顶部展示语言分布饼图
 */
export function TrendingList({
  repos,
  loading,
  error,
  onRetry,
  onLoadMore,
  hasMore = false,
  loadingMore = false,
}: TrendingListProps) {
  /** 下拉刷新状态 */
  const [refreshing, setRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartY = useRef(0);
  const pullThreshold = 80; // 下拉触发阈值

  /** 从 repos 聚合语言分布 */
  const languageData = useMemo(() => {
    if (loading || repos.length === 0) return [];
    return aggregateLanguages(repos);
  }, [repos, loading]);

  // ── 下拉刷新（移动端） ────────────────────────
  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (containerRef.current && containerRef.current.scrollTop <= 0) {
        touchStartY.current = e.touches[0].clientY;
      }
    },
    [],
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (refreshing) return;
      if (containerRef.current && containerRef.current.scrollTop <= 0) {
        const distance = e.touches[0].clientY - touchStartY.current;
        if (distance > 0 && distance < 150) {
          setPullDistance(distance);
        }
      }
    },
    [refreshing],
  );

  const handleTouchEnd = useCallback(async () => {
    if (pullDistance >= pullThreshold && onRetry) {
      setRefreshing(true);
      onRetry();
      // 模拟刷新动画
      await new Promise((resolve) => setTimeout(resolve, 800));
      setRefreshing(false);
    }
    setPullDistance(0);
  }, [pullDistance, onRetry]);

  // ── 无限滚动加载更多 ──────────────────────────
  useEffect(() => {
    if (!onLoadMore || !hasMore || loadingMore) return;

    const handleScroll = () => {
      const scrollY = window.scrollY + window.innerHeight;
      const docHeight = document.documentElement.scrollHeight;
      if (scrollY >= docHeight - 300) {
        onLoadMore();
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [onLoadMore, hasMore, loadingMore]);

  // 加载态
  if (loading && repos.length === 0) {
    return <SkeletonCardList count={9} />;
  }

  // 错误态
  if (error && repos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-red-800 bg-red-900/20 py-16">
        <svg
          className="mb-4 h-12 w-12 text-red-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <p className="text-sm text-red-300">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
            style={{ minHeight: 48 }}
          >
            重试
          </button>
        )}
      </div>
    );
  }

  // 空态
  if (repos.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700 bg-slate-800/30 py-16">
        <svg
          className="mb-4 h-12 w-12 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <p className="text-sm text-slate-500">暂无数据</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* 下拉刷新指示器 */}
      {pullDistance > 0 && (
        <div
          className="flex items-center justify-center py-3 transition-all"
          style={{ height: Math.min(pullDistance, 60) }}
        >
          <div
            className={`h-5 w-5 rounded-full border-2 border-primary-500 ${
              refreshing ? "animate-spin border-t-transparent" : ""
            }`}
          />
          <span className="ml-2 text-xs text-slate-400">
            {refreshing
              ? "刷新中..."
              : pullDistance >= pullThreshold
                ? "释放刷新"
                : "下拉刷新"}
          </span>
        </div>
      )}

      {/* 语言分布饼图 */}
      {languageData.length > 0 && (
        <div className="mb-6 rounded-xl border border-slate-700 bg-slate-800/50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">
            语言分布
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={languageData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="count"
                nameKey="language"
                label={({ language, count }) =>
                  `${language} (${count})`
                }
                labelLine={false}
              >
                {languageData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #475569",
                  borderRadius: "8px",
                  color: "#e2e8f0",
                  fontSize: "12px",
                }}
                formatter={(value: number, name: string) => [
                  `${value} 个`,
                  name,
                ]}
              />
              <Legend
                wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 卡片网格 */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {repos.map((repo) => (
          <RepoTrendingCard key={repo.id} repo={repo} />
        ))}
      </div>

      {/* 加载更多指示器 */}
      {loadingMore && (
        <div className="mt-6 flex justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
        </div>
      )}

      {/* 加载更多按钮（桌面端手动触发） */}
      {!loadingMore && hasMore && onLoadMore && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={onLoadMore}
            className="rounded-lg border border-slate-600 bg-slate-700/50 px-6 py-2.5 text-sm text-slate-300 transition-colors hover:bg-slate-700 hover:text-slate-100"
            style={{ minHeight: 48 }}
          >
            加载更多
          </button>
        </div>
      )}
    </div>
  );
}
