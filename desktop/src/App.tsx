import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, HashRouter } from "react-router-dom";
import { TrendingPage } from "./pages/TrendingPage";
import { RepoDetailPage } from "./pages/RepoDetailPage";
import { AuthPage } from "./pages/AuthPage";
import { Layout } from "./components/Layout";
import { LazyFallback } from "./components/LazyFallback";

// Phase 4: 路由级代码分割 (React.lazy + Suspense)
const SearchPage = lazy(() =>
  import("./pages/SearchPage").then((m) => ({ default: m.SearchPage })),
);
const CollectionsPage = lazy(() =>
  import("./pages/CollectionsPage").then((m) => ({ default: m.CollectionsPage })),
);
const SettingsPage = lazy(() =>
  import("./pages/SettingsPage").then((m) => ({ default: m.SettingsPage })),
);
const AdminPage = lazy(() =>
  import("./pages/AdminPage").then((m) => ({ default: m.AdminPage })),
);
const RecommendedPage = lazy(() =>
  import("./pages/RecommendedPage").then((m) => ({ default: m.RecommendedPage })),
);

function isHarmonyOS(): boolean {
  if (typeof window === "undefined") return false;
  const win = window as any;
  return win.__HARMONY__ !== undefined || /HarmonyOS/i.test(navigator.userAgent);
}

function App() {
  const isMobile =
    typeof (window as any).Capacitor !== "undefined" ||
    window.location.protocol === "file:" ||
    isHarmonyOS();

  const Router = isMobile ? HashRouter : BrowserRouter;

  return (
    <Router>
      <Routes>
        <Route path="/auth" element={<AuthPage />} />

        <Route
          path="*"
          element={
            <Layout>
              <Suspense fallback={<LazyFallback />}>
                <Routes>
                  <Route path="/" element={<TrendingPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/collections" element={<CollectionsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/repo/:owner/:repo" element={<RepoDetailPage />} />
                  <Route path="/recommended" element={<RecommendedPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                </Routes>
              </Suspense>
            </Layout>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
