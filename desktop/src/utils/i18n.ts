import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// 中文
import zhCommon from "../locales/zh/common.json";
import zhTrending from "../locales/zh/trending.json";
import zhDetail from "../locales/zh/detail.json";
import zhAuth from "../locales/zh/auth.json";
import zhSettings from "../locales/zh/settings.json";
import zhSearch from "../locales/zh/search.json";
import zhAdmin from "../locales/zh/admin.json";

// 英文
import enCommon from "../locales/en/common.json";
import enTrending from "../locales/en/trending.json";
import enDetail from "../locales/en/detail.json";
import enAuth from "../locales/en/auth.json";
import enSettings from "../locales/en/settings.json";
import enSearch from "../locales/en/search.json";
import enAdmin from "../locales/en/admin.json";

// 日文
import jaCommon from "../locales/ja/common.json";
import jaTrending from "../locales/ja/trending.json";
import jaDetail from "../locales/ja/detail.json";
import jaAuth from "../locales/ja/auth.json";
import jaSettings from "../locales/ja/settings.json";
import jaSearch from "../locales/ja/search.json";
import jaAdmin from "../locales/ja/admin.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      zh: {
        common: zhCommon,
        trending: zhTrending,
        detail: zhDetail,
        auth: zhAuth,
        settings: zhSettings,
        search: zhSearch,
        admin: zhAdmin,
      },
      en: {
        common: enCommon,
        trending: enTrending,
        detail: enDetail,
        auth: enAuth,
        settings: enSettings,
        search: enSearch,
        admin: enAdmin,
      },
      ja: {
        common: jaCommon,
        trending: jaTrending,
        detail: jaDetail,
        auth: jaAuth,
        settings: jaSettings,
        search: jaSearch,
        admin: jaAdmin,
      },
    },
    fallbackLng: "zh",
    defaultNS: "common",
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
      lookupLocalStorage: "devpulse_language",
    },
  });

export default i18n;
