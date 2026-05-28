import { useEffect, useState } from "react";

/**
 * 离线状态横幅组件。
 *
 * 监听 navigator.onLine + online/offline 事件，
 * 离线时在页面顶部显示黄色提示横幅，在线时自动隐藏。
 */
export function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(
    typeof navigator !== "undefined" ? !navigator.onLine : false,
  );

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="sticky top-12 z-40 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-center gap-2 rounded-lg border border-yellow-600/50 bg-yellow-900/30 px-4 py-2 text-sm text-yellow-300 backdrop-blur">
        <span className="text-base" role="img" aria-label="离线">
          📡
        </span>
        <span>当前离线，正在展示缓存数据</span>
      </div>
    </div>
  );
}
