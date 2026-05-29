import { useEffect, useState } from "react";
import { useTrendingStore } from "../stores/useTrendingStore";
import { useRecommendationStore } from "../stores/useRecommendationStore";
import { TrendingList } from "../components/TrendingList";
import { DataSourceTabs } from "../components/DataSourceTabs";
import { LanguageFilter } from "../components/LanguageFilter";
import { OfflineBanner } from "../components/OfflineBanner";
import { getTrendingCache } from "../utils/cache";
import type { TrendingSource } from "../types";

const SINCE_OPTIONS = [
  { value: "daily", label: "今日" },
  { value: "weekly", label: "本周" },
  { value: "monthly", label: "本月" },
] as const;

type TabType = "trending" | "recommended";

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

  const recItems = useRecommendationStore((s) => s.items);
  const recLoading = useRecommendationStore((s) => s.loading);
  const recMethod = useRecommendationStore((s) => s.method);
  const fetchRecommended = useRecommendationStore((s) => s.fetchRecommended);

  const [activeTab, setActiveTab] = useState<TabType>("trending");
  const [offlineDataUsed, setOfflineDataUsed] = useState(false);

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

  useEffect(() => {
    if (activeTab === "recommended") {
      fetchRecommended(25);
    }
  }, [activeTab, fetchRecommended]);

  const handleSourceChange = (newSource: TrendingSource) => {
    setSource(newSource);
  };

  // 将推荐数据转为 Trending 格式
  const recRepos = recItems.map((item) => ({
    ...item.repo,
    is_favorited: false,
  }));

  return (
    <div>
      <OfflineBanner />

      {/* 页面标题与 Tab */}
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

          <div className="flex flex-wrap items-center gap-3">
            {activeTab === "trending" && (
              <>
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
                <LanguageFilter value={language} onChange={setLanguage} />
              </>
            )}
          </div>
        </div>

        {/* Tab 切换 */}
        <div className="mt-4 flex gap-1 rounded-lg border border-slate-700 bg-slate-800/50 p-1 w-fit">
          <button
            onClick={() => setActiveTab("trending")}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "trending"
                ? "bg-primary-500 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
            style={{ minHeight: 36 }}
          >
            🔥 Trending
          </button>
          <button
            onClick={() => setActiveTab("recommended")}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "recommended"
                ? "bg-primary-500 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
            style={{ minHeight: 36 }}
          >
            🧠 为你推荐
          </button>
        </div>

        {activeTab === "trending" && (
          <div className="mt-4">
            <DataSourceTabs active={source} onChange={handleSourceChange} />
          </div>
        )}

        {activeTab === "recommended" && recMethod !== "popular" && (
          <div className="mt-4 rounded-lg bg-primary-500/10 px-4 py-2 text-sm text-primary-400">
            {recMethod === "collaborative"
              ? "基于你的浏览偏好个性化推荐"
              : recMethod === "content"
              ? "基于你的技术偏好推荐"
              : "为你推荐热门项目"}
          </div>
        )}
      </div>

      {/* 列表 */}
      {activeTab === "trending" ? (
        <TrendingList
          repos={repos}
          loading={loading}
          error={error}
          onRetry={fetchTrending}
        />
      ) : (
        <TrendingList
          repos={recRepos}
          loading={recLoading}
          error={null}
          onRetry={() => fetchRecommended(25)}
        />
      )}
    </div>
  );
}
