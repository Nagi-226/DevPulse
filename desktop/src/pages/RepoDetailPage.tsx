import { useParams, Link } from "react-router-dom";
import { useRepoDetailStore } from "../stores/useRepoDetailStore";
import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getDetailCache } from "../utils/cache";
import type { Repo } from "../types";

/**
 * 项目详情页。
 *
 * 通过 URL 参数 owner/repo 确定目标项目，调用 API 获取完整项目信息、
 * LLM 生成的摘要分析、收藏状态和 Star 趋势数据。
 * 包含收藏按钮（⭐ 切换）和 Recharts Star 趋势曲线。
 * 离线时自动使用 Dexie detail_cache 缓存数据。
 */
export function RepoDetailPage() {
  const { owner, repo: repoName } = useParams<{
    owner: string;
    repo: string;
  }>();
  const repo = useRepoDetailStore((s) => s.repo);
  const loading = useRepoDetailStore((s) => s.loading);
  const error = useRepoDetailStore((s) => s.error);
  const fetchRepo = useRepoDetailStore((s) => s.fetchRepo);

  const isFavorite = useRepoDetailStore((s) => s.isFavorite);
  const toggleFavorite = useRepoDetailStore((s) => s.toggleFavorite);
  const starHistory = useRepoDetailStore((s) => s.starHistory);
  const starHistoryLoading = useRepoDetailStore((s) => s.starHistoryLoading);
  const fetchStarHistory = useRepoDetailStore((s) => s.fetchStarHistory);

  const [offlineDataUsed, setOfflineDataUsed] = useState(false);

  useEffect(() => {
    if (!owner || !repoName) return;

    const loadData = async () => {
      const fullName = `${owner}/${repoName}`;

      // 离线优先：尝试缓存
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        try {
          const cached = await getDetailCache(fullName);
          if (cached) {
            useRepoDetailStore.setState({
              repo: cached as Repo,
              loading: false,
              error: "当前离线，正在展示缓存数据",
            });
            setOfflineDataUsed(true);
            return;
          }
        } catch {
          // 缓存不可用
        }
      }

      fetchRepo(owner, repoName);
      fetchStarHistory(owner, repoName);
    };

    loadData();
  }, [owner, repoName, fetchRepo, fetchStarHistory]);

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

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-slate-400">{error}</p>
        <Link
          to="/"
          className="mt-4 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 transition-colors"
        >
          返回首页
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  if (!repo) return null;

  const handleToggleFavorite = async () => {
    await toggleFavorite();
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* 返回链接 */}
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-primary-400 transition-colors"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        返回列表
      </Link>

      {/* 离线缓存提示 */}
      {offlineDataUsed && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-yellow-600/50 bg-yellow-900/30 px-4 py-2 text-sm text-yellow-300">
          <span>📡</span>
          <span>当前离线，正在展示缓存数据</span>
        </div>
      )}

      {/* 项目头部信息 + 收藏按钮 */}
      <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        {/* 标题行 + 收藏按钮 */}
        <div className="flex items-start justify-between">
          <h1 className="text-2xl font-bold text-white">{repo.full_name}</h1>
          <button
            onClick={handleToggleFavorite}
            className={`flex-shrink-0 rounded-lg p-2 transition-all duration-200 ${
              isFavorite
                ? "bg-yellow-400/15 text-yellow-400 hover:bg-yellow-400/25"
                : "bg-slate-700/50 text-slate-400 hover:text-yellow-400 hover:bg-slate-700"
            }`}
            aria-label={isFavorite ? "取消收藏" : "收藏项目"}
            title={isFavorite ? "取消收藏" : "收藏项目"}
          >
            <svg
              className="h-5 w-5"
              fill={isFavorite ? "currentColor" : "none"}
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={isFavorite ? 0 : 2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
              />
            </svg>
          </button>
        </div>

        <p className="mt-3 leading-relaxed text-slate-300">
          {repo.description}
        </p>

        {/* 统计信息 */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <span className="inline-flex items-center gap-1.5 text-yellow-400">
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            {fmt(repo.total_stars)} Stars
            {repo.stars_since > 0 && (
              <span className="text-emerald-400">
                (+{fmt(repo.stars_since)} 本周)
              </span>
            )}
          </span>

          <span className="inline-flex items-center gap-1.5 text-slate-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            {fmt(repo.forks)} Forks
          </span>

          {repo.open_issues !== undefined && (
            <span className="inline-flex items-center gap-1.5 text-slate-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {repo.open_issues} Issues
            </span>
          )}

          {repo.language && (
            <span className="inline-flex items-center gap-1.5 text-slate-400">
              <span className="h-3 w-3 rounded-full bg-primary-400" />
              {repo.language}
            </span>
          )}
        </div>

        {/* 日期信息 */}
        {(repo.created_at || repo.updated_at) && (
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
            {repo.created_at && (
              <span>Created: {formatDate(repo.created_at)}</span>
            )}
            {repo.updated_at && (
              <span>Updated: {formatDate(repo.updated_at)}</span>
            )}
          </div>
        )}

        {/* Topics */}
        {repo.topics.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {repo.topics.map((t) => (
              <span
                key={t}
                className="rounded-full bg-primary-500/10 px-3 py-1 text-xs text-primary-400"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {/* 外部链接 */}
        <a
          href={repo.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition-colors"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
          在 GitHub 上查看
        </a>
      </div>

      {/* Star 趋势曲线 */}
      <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <svg
            className="h-5 w-5 text-yellow-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          Star 趋势（近 30 天）
        </h2>

        {/* 加载态 */}
        {starHistoryLoading && (
          <div className="mt-4 flex items-center justify-center py-12">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
          </div>
        )}

        {/* 空态 */}
        {!starHistoryLoading && starHistory.length === 0 && (
          <div className="mt-4 flex flex-col items-center justify-center py-12 text-slate-500">
            <svg
              className="mb-3 h-10 w-10"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            <p className="text-sm">Star 历史数据积累中...</p>
          </div>
        )}

        {/* 图表 */}
        {!starHistoryLoading && starHistory.length > 0 && (
          <div className="mt-4">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={starHistory}
                margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#334155"
                  strokeOpacity={0.5}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  tickFormatter={(val: string) => {
                    const d = new Date(val);
                    return `${d.getMonth() + 1}/${d.getDate()}`;
                  }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  tickFormatter={(val: number) => fmt(val)}
                  width={50}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #475569",
                    borderRadius: "8px",
                    color: "#e2e8f0",
                    fontSize: "12px",
                  }}
                  formatter={(value: number) => [
                    `${value.toLocaleString()} stars`,
                    "Stars",
                  ]}
                  labelFormatter={(label: string) => `日期: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="stars"
                  stroke="#818cf8"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{
                    r: 3,
                    fill: "#818cf8",
                    stroke: "#1e293b",
                    strokeWidth: 2,
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* LLM 摘要区域 */}
      {repo.readme_summary && (
        <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <svg
              className="h-5 w-5 text-primary-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            AI 摘要
          </h2>

          {/* 概述 */}
          <p className="mt-3 leading-relaxed text-slate-300">
            {repo.readme_summary}
          </p>

          {/* 核心要点 */}
          {repo.key_points && repo.key_points.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-slate-400">核心要点</h3>
              <ul className="mt-2 space-y-1.5">
                {repo.key_points.map((kp, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-slate-300"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-400" />
                    {kp}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 标签 */}
          {repo.tags && repo.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {repo.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-md bg-slate-700/50 px-2.5 py-1 text-xs text-slate-300"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
