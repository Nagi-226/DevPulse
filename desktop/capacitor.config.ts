import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.devpulse.app",
  appName: "DevPulse",
  webDir: "dist",
  server: {
    // Android 开发时启用热重载（连 PC 端 dev server）
    // 生产构建时注释掉此行
    // url: "http://192.168.1.100:1420",
    // cleartext: true,
  },
  android: {
    allowMixedContent: true,
    // 允许 Capacitor 在 Android 上访问 HTTP（开发环境）
    // 生产环境应使用 HTTPS
  },
};

export default config;
