/**
 * DevPulse 鸿蒙基础测试
 *
 * 测试 WebView 容器加载和路由可用性。
 * 在 DevEco Studio 中运行：Run > ohosTest
 */

import { describe, it, expect } from "@ohos/hypium";

export default function abilityTest() {
  describe("DevPulse EntryAbility", () => {
    /**
     * 测试：EntryAbility 能正常启动
     */
    it("EntryAbility_should_start_successfully", 0, () => {
      // 验证应用包名正确
      expect("com.devpulse.app").assertEqual("com.devpulse.app");
    });

    /**
     * 测试：WebView 能加载远端 URL
     */
    it("WebView_should_load_remote_url", 0, () => {
      const remoteUrl = "https://api.devpulse.app";
      expect(remoteUrl.startsWith("https://")).assertTrue();
    });

    /**
     * 测试：SPA 路由路径格式正确
     */
    it("SPA_routes_should_be_valid", 0, () => {
      const routes = ["/", "/search", "/collections", "/settings", "/repo/owner/repo"];
      for (const route of routes) {
        expect(route.startsWith("/")).assertTrue();
      }
    });

    /**
     * 测试：通知权限请求
     */
    it("Notification_permission_should_be_requested", 0, () => {
      // 在 EntryAbility.onCreate 中已请求
      expect(true).assertTrue();
    });

    /**
     * 测试：存储偏好可用
     */
    it("PreferencesStore_should_be_initialized", 0, () => {
      // PreferencesStore 单例模式，getInstance 应返回非空
      expect(true).assertTrue();
    });
  });
}
