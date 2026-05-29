import { useEffect, useState } from "react";
import { useNotificationStore } from "../stores/useNotificationStore";
import { useAuthStore } from "../stores/useAuthStore";
import { getCacheStats, clearAllCache } from "../utils/cache";
import { api } from "../utils/api-client";
import { LanguageSwitcher } from "../components/LanguageSwitcher";

export function SettingsPage() {
  const enabled = useNotificationStore((s) => s.enabled);
  const toggle = useNotificationStore((s) => s.toggle);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const [pushWeekly, setPushWeekly] = useState(true);
  const [pushImportant, setPushImportant] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [cacheStats, setCacheStats] = useState({
    trendingCount: 0,
    detailCount: 0,
  });
  const [clearing, setClearing] = useState(false);

  const loadCacheStats = async () => {
    const stats = await getCacheStats();
    setCacheStats(stats);
  };

  useEffect(() => {
    loadCacheStats();
    if (user) {
      setPushWeekly(user.push_weekly_report ?? true);
      setPushImportant(user.push_important_project ?? false);
    }
  }, [user]);

  const handleClearCache = async () => {
    setClearing(true);
    try {
      await clearAllCache();
      await loadCacheStats();
    } finally {
      setClearing(false);
    }
  };

  const syncPreferences = async (
    key: "push_weekly_report" | "push_important_project",
    value: boolean,
  ) => {
    if (!isAuthenticated) return;
    setSyncing(true);
    try {
      await api.updatePreferences({ [key]: value });
    } catch {
      // 静默失败
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-white">设置</h1>
      <p className="mt-1 text-sm text-slate-400">
        管理通知偏好和离线缓存
      </p>

      {/* 界面语言 (Phase 4) */}
      <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        <h2 className="text-base font-semibold text-white">界面语言</h2>
        <p className="mt-1 text-sm text-slate-400">选择显示语言</p>
        <div className="mt-3">
          <LanguageSwitcher />
        </div>
      </div>

      {/* 推送通知开关 */}
      <div className="mt-4 rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">
              推送通知
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              新周报生成时通过系统通知提醒
            </p>
          </div>
          <button
            onClick={toggle}
            role="switch"
            aria-checked={enabled}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-800 ${
              enabled ? "bg-primary-500" : "bg-slate-600"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                enabled ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {isAuthenticated && (
          <div className="mt-4 space-y-3 border-t border-slate-700 pt-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">周报推送</span>
              <button
                onClick={() => {
                  const next = !pushWeekly;
                  setPushWeekly(next);
                  syncPreferences("push_weekly_report", next);
                }}
                role="switch"
                aria-checked={pushWeekly}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  pushWeekly ? "bg-primary-500" : "bg-slate-600"
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                    pushWeekly ? "translate-x-[18px]" : "translate-x-[4px]"
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">重要项目推送</span>
              <button
                onClick={() => {
                  const next = !pushImportant;
                  setPushImportant(next);
                  syncPreferences("push_important_project", next);
                }}
                role="switch"
                aria-checked={pushImportant}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  pushImportant ? "bg-primary-500" : "bg-slate-600"
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                    pushImportant ? "translate-x-[18px]" : "translate-x-[4px]"
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center gap-2 text-xs">
              {syncing ? (
                <>
                  <span className="h-2 w-2 animate-pulse rounded-full bg-yellow-400" />
                  <span className="text-slate-500">同步中...</span>
                </>
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="text-slate-500">偏好已云同步</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 离线缓存 */}
      <div className="mt-4 rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        <h2 className="text-base font-semibold text-white">
          离线缓存
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          断网时自动使用本地缓存数据
        </p>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="rounded-lg border border-slate-700 bg-slate-800/80 p-3 text-center">
            <p className="text-2xl font-bold text-primary-400">
              {cacheStats.trendingCount}
            </p>
            <p className="mt-1 text-xs text-slate-500">Trending 缓存</p>
          </div>
          <div className="rounded-lg border border-slate-700 bg-slate-800/80 p-3 text-center">
            <p className="text-2xl font-bold text-emerald-400">
              {cacheStats.detailCount}
            </p>
            <p className="mt-1 text-xs text-slate-500">详情缓存</p>
          </div>
        </div>

        <button
          onClick={handleClearCache}
          disabled={clearing}
          className="mt-4 w-full rounded-lg border border-slate-600 bg-slate-700/50 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700 hover:text-slate-100 disabled:opacity-50"
          style={{ minHeight: 48 }}
        >
          {clearing ? "清除中..." : "清除全部缓存"}
        </button>
      </div>

      {/* 关于 */}
      <div className="mt-4 rounded-xl border border-slate-700 bg-slate-800/50 p-6">
        <h2 className="text-base font-semibold text-white">关于</h2>
        <p className="mt-2 text-sm text-slate-400">
          DevPulse v0.4.0 — GitHub Trending AI/ML 周报
        </p>
        <p className="mt-1 text-xs text-slate-500">
          数据来源: GitHub Trending · AI 摘要: LLM 驱动
        </p>
      </div>
    </div>
  );
}
