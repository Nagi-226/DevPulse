import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { OfflineBanner } from "./OfflineBanner";
import { useAuthStore } from "../stores/useAuthStore";

type NavIconType = "search" | "star" | "settings" | "admin";

const NAV_ITEMS = [
  { label: "首页", path: "/" },
  { label: "搜索", path: "/search", icon: "search" as NavIconType },
  { label: "我的收藏", path: "/collections", icon: "star" as NavIconType },
  { label: "设置", path: "/settings", icon: "settings" as NavIconType },
] as const;

function NavIcon({ icon }: { icon: NavIconType }) {
  if (icon === "search") {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    );
  }
  if (icon === "star") {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    );
  }
  if (icon === "settings") {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    );
  }
  if (icon === "admin") {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    );
  }
  return null;
}

function OnlineIndicator() {
  const [online, setOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <span
      className={`inline-flex h-2 w-2 rounded-full ${
        online ? "bg-emerald-400" : "bg-red-400"
      }`}
      title={online ? "已连接" : "离线"}
    />
  );
}

function isHarmonyOS(): boolean {
  if (typeof window === "undefined") return false;
  const win = window as any;
  return (
    win.__HARMONY__ !== undefined ||
    /HarmonyOS/i.test(navigator.userAgent)
  );
}

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const harmonyMode = isHarmonyOS();
  const isAuthPage = location.pathname === "/auth";
  const isAdmin = user?.role === "admin";

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-900 text-slate-200">
      {!harmonyMode && (
        <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-slate-900/80">
          <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
            <Link
              to="/"
              className="flex items-center gap-2 text-xl font-bold tracking-tight text-white hover:text-primary-400 transition-colors"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-sm font-extrabold text-white">
                DP
              </span>
              DevPulse
            </Link>

            <div className="flex items-center gap-3">
              <ul className="flex items-center gap-1">
                {NAV_ITEMS.map((item) => {
                  const isActive =
                    item.path === "/"
                      ? location.pathname === "/"
                      : location.pathname.startsWith(item.path);
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-slate-800 text-primary-400"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                        }`}
                      >
                        {"icon" in item && <NavIcon icon={item.icon} />}
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
                {/* Phase 4: Admin 入口 */}
                {isAdmin && (
                  <li>
                    <Link
                      to="/admin"
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        location.pathname.startsWith("/admin")
                          ? "bg-slate-800 text-primary-400"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                      }`}
                    >
                      <NavIcon icon="admin" />
                      管理
                    </Link>
                  </li>
                )}
              </ul>

              <div className="mx-1 h-5 w-px bg-slate-700" />

              {isAuthPage ? null : isAuthenticated ? (
                <div className="flex items-center gap-2">
                  <Link
                    to="/settings"
                    className="text-sm text-slate-300 hover:text-primary-400 transition-colors"
                    title={user?.email}
                  >
                    {user?.display_name || user?.email?.split("@")[0] || "用户"}
                    {isAdmin && (
                      <span className="ml-1 rounded bg-primary-500/20 px-1 py-0.5 text-xs text-primary-400">
                        admin
                      </span>
                    )}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="rounded-lg px-2 py-1 text-xs text-slate-500 hover:text-red-400 transition-colors"
                  >
                    退出
                  </button>
                </div>
              ) : (
                <Link
                  to="/auth"
                  className="rounded-lg border border-primary-500/50 px-3 py-1.5 text-sm text-primary-400 hover:bg-primary-500/10 transition-colors"
                >
                  登录
                </Link>
              )}

              <OnlineIndicator />
            </div>
          </nav>
        </header>
      )}

      <OfflineBanner />

      <main
        className={`mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8 ${
          harmonyMode ? "safe-area-padding-top" : ""
        }`}
      >
        {children}
      </main>

      {!harmonyMode && (
        <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
          DevPulse &mdash; AI 潮汐 &middot; GitHub Trending 周报
        </footer>
      )}
    </div>
  );
}
