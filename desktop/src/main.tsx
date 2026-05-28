import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Capacitor 状态栏样式适配
if (typeof (window as any).Capacitor !== "undefined") {
  const { Capacitor } = window as any;
  if (Capacitor.getPlatform() === "android") {
    // Android 沉浸式状态栏
    Capacitor.Plugins.StatusBar?.setOverlaysWebView({ overlay: true });
    Capacitor.Plugins.StatusBar?.setBackgroundColor({ color: "#0f172a" });
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);