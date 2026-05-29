import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import "./utils/i18n";

// ── Sentry 初始化 (Phase 4) ─────────────────────
const sentryDsn =
  typeof import.meta !== "undefined" &&
  (import.meta as any).env?.VITE_SENTRY_DSN;
if (sentryDsn) {
  import("@sentry/react").then((Sentry) => {
    Sentry.init({
      dsn: sentryDsn,
      environment:
        (typeof import.meta !== "undefined" &&
          (import.meta as any).env?.VITE_ENVIRONMENT) ||
        "production",
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
      ],
      tracesSampleRate: 0.2,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
    });
  });
}

// Capacitor 状态栏样式适配
if (typeof (window as any).Capacitor !== "undefined") {
  const { Capacitor } = window as any;
  if (Capacitor.getPlatform() === "android") {
    Capacitor.Plugins.StatusBar?.setOverlaysWebView({ overlay: true });
    Capacitor.Plugins.StatusBar?.setBackgroundColor({ color: "#0f172a" });
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
