import { useEffect, useState } from "react";
import { useTrendingStore } from "../stores/useTrendingStore";
import { TrendingList } from "../components/TrendingList";
import { DataSourceTabs } from "../components/DataSourceTabs";
import { LanguageFilter } from "../components/LanguageFilter";
import { OfflineBanner } from "../components/OfflineBanner";
import { getTrendingCache } from "../utils/cache";
import type { TrendingSource } from "../types";

/** 时间范围选项 */
const SINCE_OPTIONS = [
  { value: "daily", label: "今日" },
  { value: "weekly", label: "本周" },
  { value: "monthly", label: "本月" },
] as const;

/**
 * GitHub Trending 周报列表页（增强版）。
 *
 * 新增功能：
 * - 数据源切换 Tab（GitHub/GitLab/Gitee）
 * - 20+ 语言筛选下拉
 * - 移动端下拉刷新 + 上拉加载更多
 * - 离线缓存自动降级
 */
export function TrendingPage() {
  const repos = useTrendingStore((s) => s.repos);
  const loading = useTrendingStore((s) => s.loading);
  const error = useTrendingStore((s) => s.error);
  const language = useTrendingStore((s) => s.language);
  const since = useTrendingStore((s) => s.since);
  const source = useTrendingStore((s) => s.source);
  const fetchTrending = useTrendingStore((s) => s.fetchTrending);
  const setLanguage = useTrendingStore((s) => s.setLanguage);
  const setSince = useTrendingStore((s) => s.setSince);
  const setSource = useTrendingStore((s) => s.setSource);

  const [offlineDataUsed, setOfflineDataUsed] = useState(false);

  // 首次加载
  useEffect(() => {
    const loadData = async () => {
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        try {
          const cached = await getTrendingCache(since, language);
          if (cached) {
            setOfflineDataUsed(true);
            useTrendingStore.setState({
              repos: (cached as { items: typeof repos }).items ?? [],
              loading: false,
              error: "当前离线，正在展示缓存数据",
            });
            return;
          }
        } catch {
          // 缓存不可用
        }
      }
      fetchTrending();
    };

    loadData();
  }, [fetchTrending, since, language, source]);

  // 数据源切换
  const handleSourceChange = (newSource: TrendingSource) => {
    setSource(newSource);
  };

  return (
    <div>
      <OfflineBanner />

      {/* 页面标题与过滤器 */}
      <div className="mb-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white sm:text-3xl">
              开源项目 Trending 周报
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              AI/ML 领域最受关注的开源项目
              {offlineDataUsed && (
                <span className="ml-2 text-yellow-400">（离线缓存）</span>
              )}
            </p>
          </div>

          {/* 时间范围 + 语言筛选 */}
          <div className="flex flex-wrap items-center gap-3">
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
                  style={{ minHeight: 36 }}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* 语言筛选 */}
            <LanguageFilter value={language} onChange={setLanguage} />
          </div>
        </div>

        {/* 数据源 Tab */}
        <div className="mt-4">
          <DataSourceTabs active={source} onChange={handleSourceChange} />
        </div>
      </div>

      {/* 项目列表 */}
      <TrendingList
        repos={repos}
        loading={loading}
        error={error}
        onRetry={fetchTrending}
      />
    </div>
  );
}
