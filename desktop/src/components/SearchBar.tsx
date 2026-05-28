import { useState, useEffect, useRef, type KeyboardEvent } from "react";

/** 搜索栏组件属性 */
export interface SearchBarProps {
  /** 搜索回调 */
  onSearch: (query: string, language: string) => void;
  /** 语言筛选列表 */
  languages: string[];
  /** 防抖延迟（ms） */
  debounceMs?: number;
  /** placeholder 文本 */
  placeholder?: string;
  /** 初始值 */
  initialQuery?: string;
  initialLanguage?: string;
}

/**
 * 通用搜索栏组件。
 *
 * 输入框 + 语言下拉选择 + 防抖自动搜索。
 * 支持回车立即搜索、输入自动 300ms 防抖。
 */
export function SearchBar({
  onSearch,
  languages,
  debounceMs = 300,
  placeholder = "搜索 GitHub 项目...",
  initialQuery = "",
  initialLanguage = "",
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [language, setLanguage] = useState(initialLanguage);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** 防抖执行搜索 */
  const debouncedSearch = (q: string, lang: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      onSearch(q, lang);
    }, debounceMs);
  };

  /** 输入变化 */
  const handleInputChange = (value: string) => {
    setQuery(value);
    debouncedSearch(value, language);
  };

  /** 语言筛选变化 */
  const handleLanguageChange = (value: string) => {
    setLanguage(value);
    onSearch(query, value);
  };

  /** 回车立即搜索 */
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      if (timerRef.current) clearTimeout(timerRef.current);
      onSearch(query, language);
    }
  };

  /** 清除输入 */
  const handleClear = () => {
    setQuery("");
    if (timerRef.current) clearTimeout(timerRef.current);
    onSearch("", language);
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      {/* 搜索输入框 */}
      <div className="relative flex-1">
        {/* 搜索图标 */}
        <svg
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>

        <input
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 py-2.5 pl-10 pr-10 text-sm text-slate-200 placeholder-slate-500 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/30"
        />

        {/* 清除按钮 */}
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            aria-label="清除搜索"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* 语言筛选下拉 */}
      <select
        value={language}
        onChange={(e) => handleLanguageChange(e.target.value)}
        className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-sm text-slate-200 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/30 min-w-[120px]"
      >
        <option value="">全部语言</option>
        {languages.map((lang) => (
          <option key={lang} value={lang}>
            {lang}
          </option>
        ))}
      </select>
    </div>
  );
}
