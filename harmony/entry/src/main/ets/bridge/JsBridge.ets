/**
 * DevPulse JsBridge — JS ↔ ArkTS 双向通信桥
 *
 * 通过 Web 组件的 javaScriptProxy 和 runJavaScript 实现双向通信。
 * 前端通过 window.__HARMONY__ 全局对象调用原生能力：
 *   - __HARMONY__.showNotification(title, body)
 *   - __HARMONY__.setPreference(key, value)
 *   - __HARMONY__.getPreference(key) → Promise<string>
 *   - __HARMONY__.getDeviceInfo() → {platform, version, safeArea}
 */

import { webview } from "@kit.ArkWeb";
import { hilog } from "@kit.PerformanceAnalysisKit";

const TAG = "JsBridge";
const DOMAIN = 0x0001;

/**
 * JS Bridge 接口注册类。
 *
 * 被 @kit.ArkWeb 的 javaScriptProxy 注册后，
 * 前端可通过 window.__HARMONY__ 调用。
 */
export class JsBridgeInterface {
  private _controller: webview.WebviewController;

  constructor(controller: webview.WebviewController) {
    this._controller = controller;
  }

  /**
   * 发送鸿蒙原生通知
   */
  showNotification(title: string, body: string): void {
    hilog.info(DOMAIN, TAG, `showNotification: ${title}`);
    try {
      import("@kit.NotificationKit").then((module) => {
        const request = {
          content: {
            notificationContentType: module.notificationManager.ContentType
              .NOTIFICATION_CONTENT_BASIC_TEXT,
            normal: {
              title: title,
              text: body,
            },
          },
          id: Date.now(),
        };
        module.notificationManager.publish(request).catch((err: Error) => {
          hilog.error(DOMAIN, TAG, `Notification failed: ${err.message}`);
        });
      });
    } catch (err) {
      hilog.error(DOMAIN, TAG, `showNotification error: ${err}`);
    }
  }

  /**
   * 存储偏好设置到 @ohos.data.preferences
   */
  async setPreference(key: string, value: string): Promise<void> {
    try {
      const dataPreferences = await import("@kit.ArkData");
      const context = getContext();
      const prefs = await dataPreferences.dataPreferences.getPreferences(
        context,
        "devpulse_prefs"
      );
      await prefs.put(key, value);
      await prefs.flush();
      hilog.info(DOMAIN, TAG, `setPreference: ${key}=${value}`);
    } catch (err) {
      hilog.error(DOMAIN, TAG, `setPreference error: ${err}`);
    }
  }

  /**
   * 读取偏好设置
   */
  async getPreference(key: string): Promise<string> {
    try {
      const dataPreferences = await import("@kit.ArkData");
      const context = getContext();
      const prefs = await dataPreferences.dataPreferences.getPreferences(
        context,
        "devpulse_prefs"
      );
      const value = await prefs.get(key, "") as string;
      return value;
    } catch (err) {
      hilog.error(DOMAIN, TAG, `getPreference error: ${err}`);
      return "";
    }
  }

  /**
   * 获取设备信息
   */
  getDeviceInfo(): string {
    const info = {
      platform: "harmony",
      version: "5.0",
      userAgent: "HarmonyOS",
    };
    return JSON.stringify(info);
  }

  /**
   * 路由跳转（由前端调用，触发鸿蒙侧路由处理）
   */
  navigateTo(url: string): void {
    hilog.info(DOMAIN, TAG, `navigateTo: ${url}`);
    // 在 WebView 内通过 JS 实现 SPA 路由
    this._controller.runJavaScript(
      `window.location.hash = '${url.replace(/'/g, "\\'")}'`
    );
  }
}

/**
 * 在 Web 组件加载完成后注入 JS Bridge 初始化脚本。
 *
 * 在前端 window 对象上挂载 __HARMONY__ 全局对象，
 * 使前端可通过 window.__HARMONY__ 调用鸿蒙原生能力。
 */
export function getBridgeInitScript(): string {
  return `
    (function() {
      if (window.__HARMONY__) return;

      window.__HARMONY__ = {
        platform: 'harmony',
        version: '5.0',

        showNotification: function(title, body) {
          // 通过 javaScriptProxy 调用
          if (window.__harmonyBridge) {
            window.__harmonyBridge.showNotification(title, body);
          }
        },

        setPreference: function(key, value) {
          if (window.__harmonyBridge) {
            window.__harmonyBridge.setPreference(key, value);
          }
        },

        getPreference: function(key) {
          return new Promise(function(resolve) {
            if (window.__harmonyBridge) {
              window.__harmonyBridge.getPreference(key).then(resolve);
            } else {
              resolve('');
            }
          });
        },

        getDeviceInfo: function() {
          if (window.__harmonyBridge) {
            return JSON.parse(window.__harmonyBridge.getDeviceInfo());
          }
          return { platform: 'harmony', version: '5.0' };
        },

        navigateTo: function(url) {
          if (window.__harmonyBridge) {
            window.__harmonyBridge.navigateTo(url);
          } else {
            window.location.hash = url;
          }
        }
      };

      // 向鸿蒙侧通知 JS Bridge 已就绪
      console.log('[JsBridge] __HARMONY__ initialized');
    })();
  `;
}
