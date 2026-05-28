import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCollectionsStore } from "../stores/useCollectionsStore";
import { SkeletonCardList } from "../components/SkeletonCard";

/**
 * 收藏列表页。
 *
 * 从 API 获取收藏列表，以卡片式网格展示。
 * 空状态："还没有收藏任何项目"。
 * 点击卡片跳转到项目详情页。
 */
export function CollectionsPage() {
  const navigate = useNavigate();
  const favorites = useCollectionsStore((s) => s.favorites);
  const loading = useCollectionsStore((s) => s.loading);
  const error = useCollectionsStore((s) => s.error);
  const fetchFavorites = useCollectionsStore((s) => s.fetchFavorites);
  const unstar = useCollectionsStore((s) => s.unstar);

  useEffect(() => {
    fetchFavorites();
  }, [fetchFavorites]);

  /** 格式化数字 */
  const fmt = (n: number): string => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return String(n);
  };

  /** 格式化日期 */
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toISOString().slice(0, 10);
    } catch {
      return "";
    }
  };

  const handleCardClick = (owner: string, name: string) => {
    navigate(`/repo/${owner}/${name}`);
  };

  const handleUnstar = async (e: React.MouseEvent, fullName: string) => {
    e.stopPropagation();
    await unstar(fullName);
  };

  return (
    <div className="mx-auto max-w-4xl">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">我的收藏</h1>
          <p className="mt-1 text-sm text-slate-400">
            已收藏 {favorites.length} 个项目
          </p>
        </div>
      </div>

      {/* 加载态 */}
      {loading && (
        <div className="mt-6">
          <SkeletonCardList count={6} />
        </div>
      )}

      {/* 错误态 */}
      {!loading && error && (
        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-red-800 bg-red-900/20 py-16">
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
          <button
            onClick={fetchFavorites}
            className="mt-4 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-600"
          >
            重试
          </button>
        </div>
      )}

      {/* 空状态 */}
      {!loading && !error && favorites.length === 0 && (
        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-slate-700 bg-slate-800/30 py-16">
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
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
            />
          </svg>
          <p className="text-sm text-slate-500">还没有收藏任何项目</p>
          <p className="mt-1 text-xs text-slate-600">
            在项目详情页点击收藏按钮即可添加到此处
          </p>
        </div>
      )}

      {/* 收藏列表 */}
      {!loading && !error && favorites.length > 0 && (
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {favorites.map((item) => (
            <article
              key={item.id}
              onClick={() => handleCardClick(item.owner, item.name)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ")
                  handleCardClick(item.owner, item.name);
              }}
              tabIndex={0}
              role="button"
              aria-label={`查看 ${item.full_name} 详情`}
              className="group cursor-pointer rounded-xl border border-slate-700 bg-slate-800/50 p-5 transition-all duration-200 hover:scale-[1.02] hover:border-primary-500/50 hover:bg-slate-800 hover:shadow-lg hover:shadow-primary-500/10 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {/* 项目名称 + 取消收藏 */}
              <div className="flex items-start justify-between">
                <h3 className="text-base font-semibold text-white group-hover:text-primary-400 transition-colors">
                  {item.full_name}
                </h3>
                <button
                  onClick={(e) => handleUnstar(e, item.full_name)}
                  className="flex-shrink-0 rounded p-1 text-yellow-400 hover:bg-slate-700 transition-colors"
                  aria-label={`取消收藏 ${item.full_name}`}
                  title="取消收藏"
                >
                  <svg
                    className="h-5 w-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </button>
              </div>

              {/* 描述 */}
              {item.description && (
                <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-400">
                  {item.description}
                </p>
              )}

              {/* 底部信息 */}
              <div className="mt-3 flex flex-wrap items-center justify-between">
                <div className="flex items-center gap-3 text-xs">
                  {/* Stars */}
                  <span className="flex items-center gap-1 text-yellow-400">
                    <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {fmt(item.total_stars)}
                  </span>

                  {/* Language */}
                  {item.language && (
                    <span className="flex items-center gap-1 text-slate-400">
                      <span className="h-2 w-2 rounded-full bg-primary-400" />
                      {item.language}
                    </span>
                  )}
                </div>

                {/* 收藏时间 */}
                {item.created_at && (
                  <span className="text-xs text-slate-500">
                    {formatDate(item.created_at)}
                  </span>
                )}
              </div>

              {/* Tags */}
              {item.tags && item.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {item.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-primary-500/10 px-2 py-0.5 text-xs text-primary-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
