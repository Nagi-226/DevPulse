import { useEffect, useState } from "react";
import { useAdminStore } from "../stores/useAdminStore";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type AdminTab = "dashboard" | "users" | "reviews";

export function AdminPage() {
  const dashboard = useAdminStore((s) => s.dashboard);
  const dashboardLoading = useAdminStore((s) => s.dashboardLoading);
  const fetchDashboard = useAdminStore((s) => s.fetchDashboard);
  const users = useAdminStore((s) => s.users);
  const usersLoading = useAdminStore((s) => s.usersLoading);
  const fetchUsers = useAdminStore((s) => s.fetchUsers);
  const toggleUserBan = useAdminStore((s) => s.toggleUserBan);
  const updateUserRole = useAdminStore((s) => s.updateUserRole);
  const pendingReviews = useAdminStore((s) => s.pendingReviews);
  const reviewsLoading = useAdminStore((s) => s.reviewsLoading);
  const fetchPendingReviews = useAdminStore((s) => s.fetchPendingReviews);
  const approveReview = useAdminStore((s) => s.approveReview);
  const rejectReview = useAdminStore((s) => s.rejectReview);
  const triggerCrawl = useAdminStore((s) => s.triggerCrawl);

  const [activeTab, setActiveTab] = useState<AdminTab>("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchUsers();
    fetchPendingReviews();
  }, [fetchDashboard, fetchUsers, fetchPendingReviews]);

  const fmt = (n: number): string => {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return String(n);
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">管理后台</h1>
        <p className="mt-1 text-sm text-slate-400">运营数据看板与用户管理</p>
      </div>

      {/* Tab */}
      <div className="mb-6 flex gap-1 rounded-lg border border-slate-700 bg-slate-800/50 p-1 w-fit">
        {(["dashboard", "users", "reviews"] as AdminTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-primary-500 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
            style={{ minHeight: 36 }}
          >
            {tab === "dashboard" ? "📊 看板" : tab === "users" ? "👥 用户" : "✅ 审核"}
          </button>
        ))}
      </div>

      {/* Dashboard */}
      {activeTab === "dashboard" && (
        <div>
          {dashboardLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : dashboard ? (
            <>
              {/* 统计卡片 */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                  { label: "DAU", value: dashboard.summary.dau, color: "text-blue-400", bg: "bg-blue-500/10" },
                  { label: "阅读量", value: fmt(dashboard.summary.page_views), color: "text-emerald-400", bg: "bg-emerald-500/10" },
                  { label: "收藏", value: fmt(dashboard.summary.favorites_count), color: "text-yellow-400", bg: "bg-yellow-500/10" },
                  { label: "LLM成本", value: `$${dashboard.summary.llm_cost.toFixed(2)}`, color: "text-red-400", bg: "bg-red-500/10" },
                ].map((card) => (
                  <div
                    key={card.label}
                    className={`rounded-xl border border-slate-700 ${card.bg} p-4`}
                  >
                    <p className="text-xs text-slate-400">{card.label}</p>
                    <p className={`mt-1 text-2xl font-bold ${card.color}`}>
                      {card.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* 趋势图 */}
              {dashboard.daily_trend.length > 0 && (
                <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
                  <h2 className="text-lg font-semibold text-white">📈 周报阅读趋势（30天）</h2>
                  <div className="mt-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={dashboard.daily_trend}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 11, fill: "#94a3b8" }}
                        />
                        <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#1e293b",
                            border: "1px solid #475569",
                            borderRadius: "8px",
                            color: "#e2e8f0",
                          }}
                        />
                        <Line type="monotone" dataKey="page_views" stroke="#818cf8" strokeWidth={2} dot={false} name="阅读量" />
                        <Line type="monotone" dataKey="dau" stroke="#34d399" strokeWidth={2} dot={false} name="DAU" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* 爬虫触发 */}
              <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
                <h2 className="text-lg font-semibold text-white">🕷️ 爬虫管理</h2>
                <button
                  onClick={async () => {
                    setCrawling(true);
                    await triggerCrawl();
                    setCrawling(false);
                  }}
                  disabled={crawling}
                  className="mt-3 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 transition-colors disabled:opacity-50"
                  style={{ minHeight: 40 }}
                >
                  {crawling ? "触发中..." : "手动触发爬取"}
                </button>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Users */}
      {activeTab === "users" && (
        <div>
          <div className="mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") fetchUsers(1, searchQuery);
              }}
              placeholder="搜索用户..."
              className="w-full max-w-xs rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary-500 focus:outline-none"
            />
          </div>

          {usersLoading ? (
            <div className="flex items-center justify-center py-10">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 bg-slate-800/50">
                    <th className="px-4 py-3 text-left text-slate-400">邮箱</th>
                    <th className="px-4 py-3 text-left text-slate-400">名称</th>
                    <th className="px-4 py-3 text-left text-slate-400">角色</th>
                    <th className="px-4 py-3 text-left text-slate-400">状态</th>
                    <th className="px-4 py-3 text-left text-slate-400">注册日期</th>
                    <th className="px-4 py-3 text-left text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                      <td className="px-4 py-3 text-slate-200">{u.email}</td>
                      <td className="px-4 py-3 text-slate-300">{u.display_name || "-"}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded px-2 py-0.5 text-xs ${
                          u.role === "admin" ? "bg-primary-500/15 text-primary-400" : "bg-slate-700 text-slate-300"
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={u.is_active ? "text-emerald-400" : "text-red-400"}>
                          {u.is_active ? "正常" : "已封禁"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("zh-CN") : "-"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => toggleUserBan(u.id, u.is_active)}
                            className="rounded px-2 py-1 text-xs text-slate-400 hover:text-red-400 transition-colors"
                          >
                            {u.is_active ? "封禁" : "解禁"}
                          </button>
                          {u.role !== "admin" ? (
                            <button
                              onClick={() => updateUserRole(u.id, "admin")}
                              className="rounded px-2 py-1 text-xs text-slate-400 hover:text-primary-400 transition-colors"
                            >
                              升管理
                            </button>
                          ) : (
                            <button
                              onClick={() => updateUserRole(u.id, "user")}
                              className="rounded px-2 py-1 text-xs text-slate-400 hover:text-yellow-400 transition-colors"
                            >
                              降级
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <div className="py-8 text-center text-sm text-slate-500">暂无用户</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Reviews */}
      {activeTab === "reviews" && (
        <div>
          {reviewsLoading ? (
            <div className="flex items-center justify-center py-10">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : pendingReviews.length === 0 ? (
            <div className="rounded-xl border border-slate-700 bg-slate-800/30 p-8 text-center text-slate-500">
              暂无待审核项目
            </div>
          ) : (
            <div className="space-y-4">
              {pendingReviews.map((review) => (
                <div
                  key={review.id}
                  className="rounded-xl border border-slate-700 bg-slate-800/30 p-5"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-white">{review.full_name}</h3>
                      <p className="mt-1 text-sm text-slate-400">
                        置信度:{" "}
                        <span className={
                          (review.confidence_score || 0) >= 0.7
                            ? "text-emerald-400"
                            : (review.confidence_score || 0) >= 0.4
                            ? "text-yellow-400"
                            : "text-red-400"
                        }>
                          {Math.round((review.confidence_score || 0) * 100)}%
                        </span>
                      </p>
                      {review.readme_summary && (
                        <p className="mt-2 text-sm text-slate-300 max-w-2xl">
                          {review.readme_summary.slice(0, 200)}...
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      <button
                        onClick={() => approveReview(review.id)}
                        className="rounded-lg bg-emerald-500/15 px-3 py-1.5 text-sm text-emerald-400 hover:bg-emerald-500/25 transition-colors"
                      >
                        通过
                      </button>
                      <button
                        onClick={() => rejectReview(review.id)}
                        className="rounded-lg bg-red-500/15 px-3 py-1.5 text-sm text-red-400 hover:bg-red-500/25 transition-colors"
                      >
                        拒绝
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
