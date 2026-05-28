import { BrowserRouter, Routes, Route, HashRouter } from "react-router-dom";
import { TrendingPage } from "./pages/TrendingPage";
import { RepoDetailPage } from "./pages/RepoDetailPage";
import { SearchPage } from "./pages/SearchPage";
import { CollectionsPage } from "./pages/CollectionsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AuthPage } from "./pages/AuthPage";
import { Layout } from "./components/Layout";

/**
 * 检测是否在鸿蒙 WebView 环境中.
 */
function isHarmonyOS(): boolean {
  if (typeof window === "undefined") return false;
  const win = window as any;
  return win.__HARMONY__ !== undefined || /HarmonyOS/i.test(navigator.userAgent);
}

/**
 * 应用根组件。
 *
 * 多端路由适配：
 * - 桌面端 (Tauri / 浏览器) → BrowserRouter
 * - 移动端 (Capacitor Android / 鸿蒙 WebView) → HashRouter（兼容 file:// 协议）
 *
 * 路由配置：
 * - / → TrendingPage（首页）
 * - /search → SearchPage（搜索页）
 * - /collections → CollectionsPage（我的收藏）
 * - /settings → SettingsPage（设置页）
 * - /auth → AuthPage（登录/注册页，独立布局）
 * - /repo/:owner/:repo → RepoDetailPage（项目详情页）
 *
 * AuthPage 使用独立布局（无导航栏），其他页面共享 Layout。
 */
function App() {
  // 判断是否在移动端环境（Capacitor / 鸿蒙 / file://）
  const isMobile =
    typeof (window as any).Capacitor !== "undefined" ||
    window.location.protocol === "file:" ||
    isHarmonyOS();

  const Router = isMobile ? HashRouter : BrowserRouter;

  return (
    <Router>
      <Routes>
        {/* AuthPage — 独立布局（无导航栏） */}
        <Route path="/auth" element={<AuthPage />} />

        {/* 主布局路由 */}
        <Route
          path="*"
          element={
            <Layout>
              <Routes>
                <Route path="/" element={<TrendingPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/collections" element={<CollectionsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/repo/:owner/:repo" element={<RepoDetailPage />} />
              </Routes>
            </Layout>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
