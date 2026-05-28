import { useState, useRef, useEffect } from "react";
import type { LanguageOption } from "../types";

/** 预设语言列表（20+） */
const LANGUAGES: LanguageOption[] = [
  { value: "", label: "全部语言" },
  { value: "Python", label: "Python" },
  { value: "JavaScript", label: "JavaScript" },
  { value: "TypeScript", label: "TypeScript" },
  { value: "Go", label: "Go" },
  { value: "Rust", label: "Rust" },
  { value: "Java", label: "Java" },
  { value: "C++", label: "C++" },
  { value: "C", label: "C" },
  { value: "C#", label: "C#" },
  { value: "Ruby", label: "Ruby" },
  { value: "PHP", label: "PHP" },
  { value: "Swift", label: "Swift" },
  { value: "Kotlin", label: "Kotlin" },
  { value: "Dart", label: "Dart" },
  { value: "R", label: "R" },
  { value: "Julia", label: "Julia" },
  { value: "Scala", label: "Scala" },
  { value: "Haskell", label: "Haskell" },
  { value: "Elixir", label: "Elixir" },
  { value: "Clojure", label: "Clojure" },
  { value: "Lua", label: "Lua" },
  { value: "Shell", label: "Shell" },
  { value: "Vue", label: "Vue" },
  { value: "CSS", label: "CSS" },
  { value: "HTML", label: "HTML" },
  { value: "Zig", label: "Zig" },
  { value: "Jupyter Notebook", label: "Jupyter Notebook" },
];

/** LanguageFilter 组件属性 */
interface LanguageFilterProps {
  /** 当前选中的语言值 */
  value: string;
  /** 选中回调 */
  onChange: (language: string) => void;
}

/**
 * 语言筛选下拉组件（20+ 选项，支持搜索）。
 */
export function LanguageFilter({ value, onChange }: LanguageFilterProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 过滤语言
  const filtered = LANGUAGES.filter(
    (l) => !search || l.label.toLowerCase().includes(search.toLowerCase()),
  );

  // 当前选中项的标签
  const selectedLabel =
    LANGUAGES.find((l) => l.value === value)?.label || "全部语言";

  const handleSelect = (langValue: string) => {
    onChange(langValue);
    setOpen(false);
    setSearch("");
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-200 hover:border-slate-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
        style={{ minHeight: 44 }}
      >
        <span>🔤</span>
        <span className="max-w-[120px] truncate">{selectedLabel}</span>
        <svg
          className={`h-4 w-4 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 mt-2 w-60 rounded-lg border border-slate-700 bg-slate-800 shadow-xl">
          {/* 搜索输入 */}
          <div className="border-b border-slate-700 p-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索语言..."
              className="w-full rounded-md border border-slate-600 bg-slate-700/50 px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              autoFocus
            />
          </div>
          {/* 选项列表 */}
          <div className="max-h-60 overflow-y-auto py-1">
            {filtered.map((lang) => (
              <button
                key={lang.value}
                onClick={() => handleSelect(lang.value)}
                className={`flex w-full items-center px-4 py-2 text-sm transition-colors ${
                  lang.value === value
                    ? "bg-primary-500/15 text-primary-400"
                    : "text-slate-300 hover:bg-slate-700/50"
                }`}
              >
                {lang.value === value && (
                  <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                <span className={lang.value === value ? "" : "ml-6"}>{lang.label}</span>
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="px-4 py-2 text-sm text-slate-500">无匹配语言</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
