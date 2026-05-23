import { useParams, Link } from "react-router-dom";
import { useTrendingStore } from "../stores/useTrendingStore";
import { useEffect, useState } from "react";
import type { Repo } from "../types";

/**
 * 项目详情页。
 *
 * 通过 URL 参数 owner/repo 确定目标项目，展示完整的项目信息
 * 和 LLM 生成的摘要分析。
 */
export function RepoDetailPage() {
  const { owner, repo: repoName } = useParams<{
    owner: string;
    repo: string;
  }>();
  const repos = useTrendingStore((s) => s.repos);
  const fetchTrending = useTrendingStore((s) => s.fetchTrending);
  const [project, setProject] = useState<Repo | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    // 如果 store 中尚无数据，先获取
    if (repos.length === 0) {
      fetchTrending();
    }
  }, [repos.length, fetchTrending]);

  useEffect(() => {
    if (!owner || !repoName) return;

    const found = repos.find(
      (r) => r.owner === owner && r.name === repoName,
    );
    if (found) {
      setProject(found);
      setNotFound(false);
    } else if (repos.length > 0) {
      setNotFound(true);
    }
  }, [owner, repoName, repos]);

  /** 格式化数字 */
  const fmt = (n: number): string => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return String(n);
  };

  if (notFound) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-slate-400">
          未找到项目 {owner}/{repoName}
        </p>
        <Link
          to="/"
          className="mt-4 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 transition-colors"
        >
          返回首页
        </Link>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      {/* 返回链接 */}
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-primary-400 transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        返回列表
      </Link>

      {/* 项目头部信息 */}
      <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        <h1 className="text-2xl font-bold text-white">{project.full_name}</h1>
        <p className="mt-3 leading-relaxed text-slate-300">
          {project.description}
        </p>

        {/* 统计信息 */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <span className="inline-flex items-center gap-1.5 text-yellow-400">
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            {fmt(project.total_stars)} Stars
            {project.stars_since > 0 && (
              <span className="text-emerald-400">
                (+{fmt(project.stars_since)} 本周)
              </span>
            )}
          </span>

          <span className="inline-flex items-center gap-1.5 text-slate-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            {fmt(project.forks)} Forks
          </span>

          {project.language && (
            <span className="inline-flex items-center gap-1.5 text-slate-400">
              <span className="h-3 w-3 rounded-full bg-primary-400" />
              {project.language}
            </span>
          )}
        </div>

        {/* Topics */}
        {project.topics.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {project.topics.map((t) => (
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
          href={project.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          在 GitHub 上查看
        </a>
      </div>

      {/* LLM 摘要区域 */}
      {project.readme_summary && (
        <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <svg className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            AI 摘要
          </h2>

          {/* 概述 */}
          <p className="mt-3 leading-relaxed text-slate-300">
            {project.readme_summary}
          </p>

          {/* 核心要点 */}
          {project.key_points && project.key_points.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-slate-400">核心要点</h3>
              <ul className="mt-2 space-y-1.5">
                {project.key_points.map((kp, i) => (
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
          {project.tags && project.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {project.tags.map((tag) => (
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