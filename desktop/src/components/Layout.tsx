import { Link, useLocation } from "react-router-dom";

/** 顶部导航项配置 */
const NAV_ITEMS = [
  { label: "首页", path: "/" },
  { label: "关于", path: "/about" },
] as const;

/**
 * 全局页面布局组件。
 *
 * 包含固定顶部导航栏（Logo + 导航链接）和主内容区。
 * 使用 Tailwind CSS 暗色主题，响应式适配。
 *
 * @param children - 由 React Router 渲染的子路由页面
 */
export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-900 text-slate-200">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-slate-900/80">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2 text-xl font-bold tracking-tight text-white hover:text-primary-400 transition-colors"
          >
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary-500 text-sm font-extrabold text-white">
              DP
            </span>
            DevPulse
          </Link>

          {/* 导航链接 */}
          <ul className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-slate-800 text-primary-400"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </header>

      {/* 主内容区 */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* 页脚 */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        DevPulse &mdash; AI 潮汐 &middot; GitHub Trending 周报
      </footer>
    </div>
  );
}