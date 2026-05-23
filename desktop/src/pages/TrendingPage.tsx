import { useEffect } from "react";
import { useTrendingStore } from "../stores/useTrendingStore";
import { TrendingList } from "../components/TrendingList";

/** 可选编程语言列表 */
const LANGUAGES = [
  "all",
  "Python",
  "TypeScript",
  "JavaScript",
  "Go",
  "Rust",
  "C++",
  "Java",
  "Jupyter Notebook",
] as const;

/** 时间范围选项 */
const SINCE_OPTIONS = [
  { value: "daily", label: "今日" },
  { value: "weekly", label: "本周" },
  { value: "monthly", label: "本月" },
] as const;

/**
 * GitHub Trending 周报列表页。
 *
 * 展示按语言和时间范围过滤的项目排行榜卡片列表。
 * 使用 Zustand store 管理数据和加载状态。
 */
export function TrendingPage() {
  const repos = useTrendingStore((s) => s.repos);
  const loading = useTrendingStore((s) => s.loading);
  const error = useTrendingStore((s) => s.error);
  const language = useTrendingStore((s) => s.language);
  const since = useTrendingStore((s) => s.since);
  const fetchTrending = useTrendingStore((s) => s.fetchTrending);
  const setLanguage = useTrendingStore((s) => s.setLanguage);
  const setSince = useTrendingStore((s) => s.setSince);

  // 首次加载自动获取数据
  useEffect(() => {
    fetchTrending();
  }, [fetchTrending]);

  // 根据所选语言过滤
  const filteredRepos =
    language === "all"
      ? repos
      : repos.filter((r) => r.language === language);

  return (
    <div>
      {/* 页面标题与过滤器 */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            GitHub Trending 周报
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            AI/ML 领域最受关注的开源项目
          </p>
        </div>

        {/* 过滤器 */}
        <div className="flex flex-wrap gap-3">
          {/* 时间范围 */}
          <div className="flex rounded-lg border border-slate-700 bg-slate-800/50 p-0.5">
            {SINCE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setSince(opt.value)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  since === opt.value
                    ? "bg-primary-500 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* 语言选择 */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-1.5 text-sm text-slate-200 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>
                {lang === "all" ? "全部语言" : lang}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 项目列表 */}
      <TrendingList
        repos={filteredRepos}
        loading={loading}
        error={error}
        onRetry={fetchTrending}
      />
    </div>
  );
}