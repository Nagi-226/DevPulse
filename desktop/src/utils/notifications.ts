/**
 * Tauri 通知插件封装。
 *
 * 仅在 Tauri 桌面环境（window.__TAURI_INTERNALS__）下调用真实通知 API，
 * 非 Tauri 环境（浏览器 / Capacitor / 鸿蒙 WebView）降级跳过。
 */

/** 检测是否在 Tauri 桌面环境 */
function isTauri(): boolean {
  return typeof window !== "undefined" && !!(window as any).__TAURI_INTERNALS__;
}

/**
 * 请求系统通知权限。
 * 在 Tauri 环境下调用 tauri-plugin-notification，非 Tauri 环境返回 false。
 */
export async function requestPermission(): Promise<boolean> {
  if (!isTauri()) return false;
  try {
    const { isPermissionGranted, requestPermission: reqPerm } = await import(
      "@tauri-apps/plugin-notification"
    );
    let granted = await isPermissionGranted();
    if (!granted) {
      const permission = await reqPerm();
      granted = permission === "granted";
    }
    return granted;
  } catch {
    return false;
  }
}

/**
 * 发送系统通知。
 * 非 Tauri 环境降级到无操作。
 *
 * @param title - 通知标题
 * @param body - 通知正文
 */
export async function sendNotification(
  title: string,
  body: string,
): Promise<void> {
  if (!isTauri()) return;
  try {
    const { sendNotification: tauriSend } = await import(
      "@tauri-apps/plugin-notification"
    );
    tauriSend({ title, body });
  } catch {
    // 通知发送失败静默降级
  }
}
