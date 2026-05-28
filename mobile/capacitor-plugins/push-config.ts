/**
 * Capacitor FCM Push Notifications 初始化和权限请求模块。
 *
 * 使用方式（在 App 入口或 mount 时调用）：
 *   import { initPushNotifications } from "../capacitor-plugins/push-config";
 *   await initPushNotifications();
 *
 * 依赖：@capacitor/push-notifications
 */

import type { PushNotificationsPlugin } from "@capacitor/push-notifications";

/**
 * 在 Capacitor 环境中初始化 FCM 推送。
 *
 * 流程：
 * 1. 请求通知权限
 * 2. 注册 FCM Token
 * 3. 监听推送事件（接收/点击）
 */
export async function initPushNotifications(): Promise<void> {
  // 仅在 Capacitor 环境中执行
  if (typeof (window as any).Capacitor === "undefined") {
    console.log("[PushConfig] Not running in Capacitor environment, skipping push init");
    return;
  }

  try {
    const { PushNotifications } = await import("@capacitor/push-notifications");

    // 请求权限
    const permStatus = await PushNotifications.requestPermissions();
    if (permStatus.receive !== "granted") {
      console.warn("[PushConfig] Push notification permission denied");
      return;
    }

    // 注册
    await PushNotifications.register();

    // 监听注册成功（获取 FCM Token）
    PushNotifications.addListener("registration", (token) => {
      console.log("[PushConfig] FCM Token:", token.value);
      // 将 token 发送到后端
      try {
        const apiBase =
          (typeof import.meta !== "undefined" &&
            (import.meta as any).env?.VITE_API_BASE) ||
          "http://127.0.0.1:8000";

        fetch(`${apiBase}/auth/fcm-token`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("devpulse_access_token") || ""}`,
          },
          body: JSON.stringify({ fcm_token: token.value }),
        }).catch(() => {
          // 静默失败
        });
      } catch {
        // silent
      }
    });

    // 监听推送到达
    PushNotifications.addListener("pushNotificationReceived", (notification) => {
      console.log("[PushConfig] Push received:", notification);
    });

    // 监听推送点击
    PushNotifications.addListener(
      "pushNotificationActionPerformed",
      (notification) => {
        console.log("[PushConfig] Push tapped:", notification);
        const data = notification.notification.data;
        if (data?.report_id) {
          // 点击通知跳转到对应周报（由 App 层处理路由）
          window.dispatchEvent(
            new CustomEvent("devpulse:open_report", {
              detail: { report_id: data.report_id },
            }),
          );
        }
      },
    );

    console.log("[PushConfig] Push notifications initialized successfully");
  } catch (err) {
    console.error("[PushConfig] Failed to init push notifications:", err);
  }
}

/**
 * 注销 FCM Token（退出登录时调用）。
 */
export async function unregisterPushNotifications(): Promise<void> {
  try {
    const { PushNotifications } = await import("@capacitor/push-notifications");
    await PushNotifications.unregister();
    console.log("[PushConfig] Push notifications unregistered");
  } catch {
    // silent
  }
}
