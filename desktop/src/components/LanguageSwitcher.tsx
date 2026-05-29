import { useTranslation } from "react-i18next";

const languages = [
  { code: "zh", label: "中文" },
  { code: "en", label: "English" },
  { code: "ja", label: "日本語" },
] as const;

/** 语言切换下拉组件 */
export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const handleChange = (lang: string) => {
    i18n.changeLanguage(lang);
    try {
      localStorage.setItem("devpulse_language", lang);
    } catch {
      // silent
    }
  };

  return (
    <select
      value={i18n.language.split("-")[0]}
      onChange={(e) => handleChange(e.target.value)}
      className="rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-1.5 text-xs text-slate-300 focus:border-primary-500 focus:outline-none cursor-pointer"
    >
      {languages.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {lang.label}
        </option>
      ))}
    </select>
  );
}
