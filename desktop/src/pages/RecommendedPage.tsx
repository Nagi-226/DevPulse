import { useEffect } from "react";
import { useRecommendationStore } from "../stores/useRecommendationStore";
import { TrendingList } from "../components/TrendingList";

/** "为你推荐"独立页面 */
export function RecommendedPage() {
  const items = useRecommendationStore((s) => s.items);
  const loading = useRecommendationStore((s) => s.loading);
  const method = useRecommendationStore((s) => s.method);
  const fetchRecommended = useRecommendationStore((s) => s.fetchRecommended);

  useEffect(() => {
    fetchRecommended(25);
  }, [fetchRecommended]);

  const repos = items.map((item) => ({
    ...item.repo,
    is_favorited: false,
  }));

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white sm:text-3xl">🧠 为你推荐</h1>
        <p className="mt-1 text-sm text-slate-400">
          {method === "collaborative"
            ? "基于你的浏览偏好个性化推荐"
            : method === "content"
            ? "基于你的技术偏好推荐"
            : "为你推荐热门项目"}
        </p>
      </div>
      <TrendingList
        repos={repos}
        loading={loading}
        error={null}
        onRetry={() => fetchRecommended(25)}
      />
    </div>
  );
}
