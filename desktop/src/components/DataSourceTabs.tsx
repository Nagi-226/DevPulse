import type { TrendingSource } from "../types";

/** Tab 配置 */
const SOURCES: { key: TrendingSource; label: string; icon: string }[] = [
  { key: "github", label: "GitHub", icon: "🐙" },
  { key: "gitlab", label: "GitLab", icon: "🦊" },
  { key: "gitee", label: "Gitee", icon: "🏮" },
];

/** DataSourceTabs 组件属性 */
interface DataSourceTabsProps {
  /** 当前激活的数据源 */
  active: TrendingSource;
  /** 切换回调 */
  onChange: (source: TrendingSource) => void;
}

/**
 * 数据源切换 Tab 组件。
 *
 * 三个 Tab：GitHub / GitLab / Gitee，点击切换触发 API 调用。
 */
export function DataSourceTabs({ active, onChange }: DataSourceTabsProps) {
  return (
    <div className="flex rounded-lg border border-slate-700 bg-slate-800/50 p-1">
      {SOURCES.map((src) => (
        <button
          key={src.key}
          onClick={() => onChange(src.key)}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-all duration-200 ${
            active === src.key
              ? "bg-primary-500 text-white shadow-sm shadow-primary-500/25"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
          }`}
          style={{ minHeight: 44 }}
          aria-pressed={active === src.key}
          title={`切换到 ${src.label} 数据源`}
        >
          <span className="mr-1.5">{src.icon}</span>
          {src.label}
        </button>
      ))}
    </div>
  );
}
