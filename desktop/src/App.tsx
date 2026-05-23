import { BrowserRouter, Routes, Route } from "react-router-dom";
import { TrendingPage } from "./pages/TrendingPage";
import { RepoDetailPage } from "./pages/RepoDetailPage";
import { Layout } from "./components/Layout";

/**
 * 应用根组件。
 *
 * 配置 React Router 路由：
 * - / → TrendingPage（首页）
 * - /repo/:owner/:repo → RepoDetailPage（项目详情页）
 * 所有页面共享 Layout 布局（顶部导航 + 内容区 + 页脚）。
 */
function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<TrendingPage />} />
          <Route path="/repo/:owner/:repo" element={<RepoDetailPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;