import { useNavigate } from "react-router-dom";
import type { Repo } from "../types";

/**
 * 项目 Trending 卡片组件。
 *
 * 展示单个 GitHub Trending 项目的核心信息：
 * 排名、Star 数、项目名称与描述、语言标签、Topics、
 * 三指标行（Stars Since / Total Stars / Forks）、
 * 创建/更新时间。
 * 点击卡片跳转到项目详情页。
 *
 * @param repo - 项目数据
 */
export function RepoTrendingCard({ repo }: { repo: Repo }) {
  const navigate = useNavigate();

  /** 格式化数字为人类可读的简写 */
  const formatStars = (n: number): string => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return String(n);
  };

  /** 格式化 ISO 日期为 YYYY-MM-DD */
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toISOString().slice(0, 10);
    } catch {
      return "";
    }
  };

  const handleClick = () => {
    navigate(`/repo/${repo.owner}/${repo.name}`);
  };

  return (
    <article
      onClick={handleClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick();
      }}
      tabIndex={0}
      role="button"
      aria-label={`查看 ${repo.full_name} 详情`}
      className="group cursor-pointer rounded-xl border border-slate-700 bg-slate-800/50 p-5 transition-all duration-200 hover:scale-[1.02] hover:border-primary-500/50 hover:bg-slate-800 hover:shadow-lg hover:shadow-primary-500/10 focus:outline-none focus:ring-2 focus:ring-primary-500"
    >
      {/* 顶部：排名 + Star 信息 */}
      <div className="flex items-start justify-between">
        {/* 排名数字 */}
        <span
          className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
            repo.trending_rank <= 3
              ? "bg-primary-500 text-white"
              : "bg-slate-700 text-slate-400"
          }`}
        >
          {repo.trending_rank}
        </span>

        {/* 三指标行：Stars Since / Total Stars / Forks */}
        <div className="flex items-center gap-3 text-xs">
          {/* Stars Since */}
          {repo.stars_since > 0 && (
            <span className="flex items-center gap-1 text-emerald-400">
              <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              +{formatStars(repo.stars_since)}
            </span>
          )}

          {/* Total Stars */}
          <span className="flex items-center gap-1 text-yellow-400">
            <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            {formatStars(repo.total_stars)}
          </span>

          {/* Forks */}
          {repo.forks > 0 && (
            <span className="flex items-center gap-1 text-slate-400">
              <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
              </svg>
              {formatStars(repo.forks)}
            </span>
          )}
        </div>
      </div>

      {/* 项目名称 */}
      <h3 className="mt-4 text-base font-semibold text-white group-hover:text-primary-400 transition-colors">
        {repo.full_name}
      </h3>

      {/* 描述 */}
      <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-slate-400">
        {repo.description}
      </p>

      {/* Tags 标签行 */}
      {repo.tags && repo.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {repo.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-primary-500/10 px-2 py-0.5 text-xs text-primary-400"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 底部：语言 + Topics + 日期 */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {repo.language && (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-700/80 px-2.5 py-0.5 text-xs text-slate-300">
            <span className="h-2 w-2 rounded-full bg-primary-400" />
            {repo.language}
          </span>
        )}

        {repo.topics.slice(0, 3).map((topic) => (
          <span
            key={topic}
            className="rounded-full bg-primary-500/10 px-2.5 py-0.5 text-xs text-primary-400"
          >
            {topic}
          </span>
        ))}

        {repo.topics.length > 3 && (
          <span className="text-xs text-slate-500">
            +{repo.topics.length - 3}
          </span>
        )}
      </div>

      {/* 创建/更新时间 */}
      {(repo.created_at || repo.updated_at) && (
        <div className="mt-2 text-xs text-slate-500">
          {repo.created_at && (
            <span>Created: {formatDate(repo.created_at)}</span>
          )}
          {repo.created_at && repo.updated_at && (
            <span className="mx-1">·</span>
          )}
          {repo.updated_at && (
            <span>Updated: {formatDate(repo.updated_at)}</span>
          )}
        </div>
      )}
    </article>
  );
}
