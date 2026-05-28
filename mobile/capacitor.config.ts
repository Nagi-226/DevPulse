import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.devpulse.app",
  appName: "DevPulse",
  webDir: "../desktop/dist",

  // Android 平台配置
  android: {
    allowMixedContent: true,
  },

  server: {
    // Capacitor 生产模式：从本地 webDir 加载
    // 开发时如需热重载，取消下面注释并指向 Vite dev server
    // url: "http://192.168.1.100:1420",
    // cleartext: true,
  },

  plugins: {
    PushNotifications: {
      presentationOptions: ["badge", "sound", "alert"],
    },
  },
};

export default config;
