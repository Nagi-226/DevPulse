import { useCallback } from "react";
import { SearchBar } from "../components/SearchBar";
import { useSearchStore } from "../stores/useSearchStore";
import { RepoTrendingCard } from "../components/RepoTrendingCard";
import { SkeletonCardList } from "../components/SkeletonCard";

/** 常用编程语言选项 */
const POPULAR_LANGUAGES = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Go",
  "Rust",
  "Java",
  "C++",
  "C",
  "C#",
  "Swift",
  "Kotlin",
  "Ruby",
  "PHP",
  "Jupyter Notebook",
  "Vue",
];

/**
 * 搜索页面。
 *
 * 包含 SearchBar 组件和搜索结果列表。
 * 空状态："输入关键词开始搜索"。
 * 无结果："未找到匹配项目"。
 */
export function SearchPage() {
  const search = useSearchStore((s) => s.search);
  const results = useSearchStore((s) => s.results);
  const loading = useSearchStore((s) => s.loading);
  const error = useSearchStore((s) => s.error);
  const total = useSearchStore((s) => s.total);
  const query = useSearchStore((s) => s.query);

  const handleSearch = useCallback(
    (q: string, lang: string) => {
      search(q, lang);
    },
    [search],
  );

  return (
    <div className="mx-auto max-w-4xl">
      {/* 页面标题 */}
      <h1 className="text-2xl font-bold text-white">搜索项目</h1>
      <p className="mt-1 text-sm text-slate-400">
        按名称、描述或标签搜索 GitHub Trending 仓库
      </p>

      {/* 搜索栏 */}
      <div className="mt-6">
        <SearchBar
          onSearch={handleSearch}
          languages={POPULAR_LANGUAGES}
          debounceMs={300}
          placeholder="搜索 GitHub 项目..."
        />
      </div>

      {/* 结果区域 */}
      <div className="mt-6">
        {/* 加载态 */}
        {loading && <SkeletonCardList count={6} />}

        {/* 错误态 */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-red-800 bg-red-900/20 py-16">
            <svg
              className="mb-4 h-12 w-12 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* 空状态：未输入关键词 */}
        {!loading && !error && !query && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700 bg-slate-800/30 py-16">
            <svg
              className="mb-4 h-12 w-12 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <p className="text-sm text-slate-500">输入关键词开始搜索</p>
          </div>
        )}

        {/* 无结果 */}
        {!loading && !error && query && results.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700 bg-slate-800/30 py-16">
            <svg
              className="mb-4 h-12 w-12 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-slate-500">未找到匹配项目</p>
            <p className="mt-1 text-xs text-slate-600">
              尝试其他关键词或切换语言筛选
            </p>
          </div>
        )}

        {/* 搜索结果 */}
        {!loading && !error && results.length > 0 && (
          <>
            {/* 结果统计 */}
            <p className="mb-4 text-sm text-slate-400">
              找到 <span className="font-semibold text-slate-200">{total}</span>{" "}
              个结果
              {query && (
                <>
                  ，关键词 "<span className="text-primary-400">{query}</span>"
                </>
              )}
            </p>

            {/* 卡片网格 */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {results.map((repo) => (
                <RepoTrendingCard key={repo.id} repo={repo} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
