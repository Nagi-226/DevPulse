/**
 * DevPulse 鸿蒙应用入口 — EntryAbility
 *
 * 负责：
 * - 应用生命周期管理（onCreate/onDestroy/onForeground/onBackground）
 * - 通知权限请求
 * - 手势返回拦截（侧滑返回）
 */

import { AbilityConstant, UIAbility, Want } from "@kit.AbilityKit";
import { hilog } from "@kit.PerformanceAnalysisKit";
import { window } from "@kit.ArkUI";

const TAG = "DevPulse";
const DOMAIN = 0x0001;

export default class EntryAbility extends UIAbility {
  /**
   * 创建时回调 — 设置主窗口 + 请求通知权限
   */
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onCreate");

    // 请求通知权限
    this.requestNotificationPermission();
  }

  onDestroy(): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onDestroy");
  }

  /**
   * 窗口创建 — 设置 WebView 容器页面
   */
  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onWindowStageCreate");

    // 主窗口加载 Index 页面（WebView 容器）
    windowStage.loadContent("pages/Index", (err) => {
      if (err.code) {
        hilog.error(DOMAIN, TAG, `Failed to load content: ${err.code}`);
        return;
      }
      hilog.info(DOMAIN, TAG, "Content loaded successfully");
    });

    // 设置安全区域适配（刘海屏）
    windowStage.getMainWindow().then((mainWindow) => {
      mainWindow.setWindowLayoutFullScreen(true);
      // 获取安全区域 insets
      const avoidArea = mainWindow.getWindowAvoidArea(
        window.AvoidAreaType.TYPE_SYSTEM
      );
      hilog.info(
        DOMAIN,
        TAG,
        `Safe area: top=${avoidArea.topRect.height}, bottom=${avoidArea.bottomRect.height}`
      );
    });
  }

  onWindowStageDestroy(): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onWindowStageDestroy");
  }

  onForeground(): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onForeground");
  }

  onBackground(): void {
    hilog.info(DOMAIN, TAG, "EntryAbility onBackground");
  }

  /**
   * 请求通知权限
   */
  private async requestNotificationPermission(): Promise<void> {
    try {
      const notificationManager = await import("@kit.NotificationKit");
      const result = await notificationManager.notificationManager.requestEnableNotification();
      hilog.info(DOMAIN, TAG, `Notification permission: ${result}`);
    } catch (err) {
      hilog.warn(DOMAIN, TAG, `Failed to request notification permission: ${err}`);
    }
  }
}
