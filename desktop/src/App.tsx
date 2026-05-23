import { useEffect, useState } from "react";

const BACKEND_HEALTH_URL = "http://localhost:8000/health";

type BackendStatus = "loading" | "online" | "offline";

export default function App() {
  const [status, setStatus] = useState<BackendStatus>("loading");

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const res = await fetch(BACKEND_HEALTH_URL);
        if (!cancelled && res.ok) {
          const data = await res.json();
          if (data.status === "ok") {
            setStatus("online");
            return;
          }
        }
      } catch {
        // backend unreachable
      }
      if (!cancelled) setStatus("offline");
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const statusColor =
    status === "online"
      ? "#22c55e"
      : status === "offline"
        ? "#ef4444"
        : "#6b7280";

  const statusLabel =
    status === "online"
      ? "后端在线"
      : status === "offline"
        ? "后端离线"
        : "检测中...";

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI 潮汐 DevPulse</h1>
        <p className="subtitle">GitHub Trending AI/ML 周报</p>
      </header>
      <main className="app-main">
        <div className="version-badge">v0.0.1</div>
        <div className="status-bar">
          <span
            className="status-dot"
            style={{ backgroundColor: statusColor }}
          />
          <span className="status-label">{statusLabel}</span>
        </div>
      </main>
    </div>
  );
}