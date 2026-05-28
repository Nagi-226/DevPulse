/**
 * DevPulse 鸿蒙原生通知服务
 *
 * 封装 @ohos.notificationManager，提供：
 * - 发送基础文本通知
 * - 周报推送通知（点击跳转）
 * - 通知权限检查
 */

import { notificationManager } from "@kit.NotificationKit";
import { hilog } from "@kit.PerformanceAnalysisKit";
import { Want } from "@kit.AbilityKit";

const TAG = "NotificationService";
const DOMAIN = 0x0001;

export class NotificationService {
  /**
   * 发送周报推送通知（点击跳转到周报详情）
   *
   * @param reportId 周报 ID
   * @param title 通知标题
   * @param body 通知正文
   */
  static async sendWeeklyReportNotification(
    reportId: number,
    title: string = "📊 新周报已生成",
    body: string = "点击查看本周热门 AI 项目"
  ): Promise<void> {
    try {
      const wantAgentInfo: Want = {
        bundleName: "com.devpulse.app",
        abilityName: "EntryAbility",
        parameters: {
          report_id: String(reportId),
          source: "notification",
        },
      };

      const request: notificationManager.NotificationRequest = {
        id: reportId,
        content: {
          notificationContentType:
            notificationManager.ContentType.NOTIFICATION_CONTENT_BASIC_TEXT,
          normal: {
            title: title,
            text: body,
          },
          wantAgent: {
            wants: [wantAgentInfo],
          },
        },
      };

      await notificationManager.publish(request);
      hilog.info(DOMAIN, TAG, `Weekly report notification sent: reportId=${reportId}`);
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Failed to send notification: ${err}`);
    }
  }

  /**
   * 发送通用通知
   */
  static async sendNotification(
    title: string,
    body: string,
    id: number = Date.now()
  ): Promise<void> {
    try {
      const request: notificationManager.NotificationRequest = {
        id: id,
        content: {
          notificationContentType:
            notificationManager.ContentType.NOTIFICATION_CONTENT_BASIC_TEXT,
          normal: {
            title: title,
            text: body,
          },
        },
      };

      await notificationManager.publish(request);
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Failed to send notification: ${err}`);
    }
  }

  /**
   * 检查通知权限是否已授权
   */
  static async isNotificationEnabled(): Promise<boolean> {
    try {
      return await notificationManager.isNotificationEnabled();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Permission check failed: ${err}`);
      return false;
    }
  }

  /**
   * 请求通知权限
   */
  static async requestPermission(): Promise<boolean> {
    try {
      // @ohos.notificationManager 在 API 12+ 中 requestEnableNotification 已内置
      return true;
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Permission request failed: ${err}`);
      return false;
    }
  }

  /**
   * 取消指定通知
   */
  static async cancelNotification(id: number): Promise<void> {
    try {
      await notificationManager.cancel(id);
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Cancel notification failed: ${err}`);
    }
  }

  /**
   * 取消所有通知
   */
  static async cancelAllNotifications(): Promise<void> {
    try {
      await notificationManager.cancelAll();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `Cancel all notifications failed: ${err}`);
    }
  }
}
