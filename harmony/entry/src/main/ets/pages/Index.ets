/**
 * DevPulse ArkUI 入口页面 — WebView 容器
 *
 * 加载远端 API 或本地 dist/ 构建产物。
 * 默认加载 https://api.devpulse.app，也可通过 API_BASE_URL 环境变量配置。
 */

import { webview } from "@kit.ArkWeb";
import { router } from "@kit.ArkUI";

// 远端 API 地址（可修改为本地 IP 用于开发调试）
const REMOTE_URL: string = "https://api.devpulse.app";

@Entry
@Component
struct Index {
  /** WebView 控制器 */
  controller: webview.WebviewController = new webview.WebviewController();

  /** 加载状态 */
  @State isLoading: boolean = true;
  @State hasError: boolean = false;

  aboutToAppear(): void {
    // 页面出现时开始加载
    this.isLoading = true;
  }

  build() {
    Column() {
      // WebView
      Web({ src: REMOTE_URL, controller: this.controller })
        .domStorageAccess(true) // 启用 localStorage/SessionStorage
        .javaScriptAccess(true) // 启用 JavaScript
        .mixedMode(webview.MixedMode.All) // 允许 HTTP/HTTPS 混合
        .zoomAccess(true) // 允许缩放
        .overviewModeAccess(true)
        .width("100%")
        .height("100%")
        .onPageBegin(() => {
          this.isLoading = true;
          this.hasError = false;
        })
        .onPageEnd(() => {
          this.isLoading = false;
        })
        .onErrorReceive((event) => {
          this.isLoading = false;
          this.hasError = true;
          console.error(`WebView error: ${event?.error?.getErrorInfo()}`);
        })
    }
    .width("100%")
    .height("100%")
    .backgroundColor("#0f172a") // slate-900 暗色背景
  }
}
