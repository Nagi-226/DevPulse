import type { Repo } from "../types";
import { RepoTrendingCard } from "./RepoTrendingCard";
import { SkeletonCardList } from "./SkeletonCard";

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
}

/**
 * Trending 项目列表组件。
 *
 * Grid 布局渲染卡片列表，支持三种状态：
 * - loading：骨架屏
 * - error：错误提示 + 重试按钮
 * - empty：暂无数据提示
 * - 正常：项目卡片网格
 */
export function TrendingList({
  repos,
  loading,
  error,
  onRetry,
}: TrendingListProps) {
  // 加载态
  if (loading) {
    return <SkeletonCardList count={9} />;
  }

  // 错误态
  if (error) {
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
          >
            重试
          </button>
        )}
      </div>
    );
  }

  // 空态
  if (repos.length === 0) {
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

  // 正常态：卡片网格
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {repos.map((repo) => (
        <RepoTrendingCard key={repo.id} repo={repo} />
      ))}
    </div>
  );
}