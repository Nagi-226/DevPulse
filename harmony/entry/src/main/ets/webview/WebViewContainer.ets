/**
 * DevPulse WebView 容器组件
 *
 * 封装 Web 组件，提供：
 * - 加载状态管理（loading/error/retry）
 * - JS Bridge 双向通信
 * - 路由拦截
 * - 错误重试
 */

import { webview } from "@kit.ArkWeb";

@Component
export struct WebViewContainer {
  /** WebView URL（默认 https://api.devpulse.app） */
  @Prop src: string = "https://api.devpulse.app";

  /** WebView 控制器 */
  controller: webview.WebviewController = new webview.WebviewController();

  /** 加载状态 */
  @State isLoading: boolean = true;
  @State hasError: boolean = false;
  @State errorMessage: string = "";

  aboutToAppear(): void {
    this.isLoading = true;
    this.initJsBridge();
  }

  /**
   * 初始化 JS Bridge — 在页面加载完成后注入
   */
  private initJsBridge(): void {
    // JS Bridge 通过 JsBridge.ets 模块在页面加载时自动注入
    // 此处保留扩展点
  }

  /**
   * 重试加载
   */
  private retry(): void {
    this.hasError = false;
    this.isLoading = true;
    this.controller.refresh();
  }

  build() {
    Stack() {
      // ── WebView ────────────────────────────
      Web({ src: this.src, controller: this.controller })
        .domStorageAccess(true)
        .javaScriptAccess(true)
        .mixedMode(webview.MixedMode.All)
        .zoomAccess(true)
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
          this.errorMessage = event?.error?.getErrorInfo() || "加载失败";
        })

      // ── 加载中遮罩 ─────────────────────────
      if (this.isLoading) {
        Column() {
          LoadingProgress()
            .width(36)
            .height(36)
            .color("#6366f1") // primary-500
          Text("加载中...")
            .fontSize(14)
            .fontColor("#94a3b8") // slate-400
            .margin({ top: 12 })
        }
        .width("100%")
        .height("100%")
        .backgroundColor("#0f172a") // slate-900
        .justifyContent(FlexAlign.Center)
      }

      // ── 错误遮罩 ───────────────────────────
      if (this.hasError && !this.isLoading) {
        Column() {
          Text("加载失败")
            .fontSize(18)
            .fontWeight(FontWeight.Bold)
            .fontColor("#f87171") // red-400
          Text(this.errorMessage)
            .fontSize(12)
            .fontColor("#94a3b8")
            .margin({ top: 8 })
            .maxLines(2)
            .textOverflow({ overflow: TextOverflow.Ellipsis })

          Button("重试")
            .margin({ top: 16 })
            .fontSize(14)
            .backgroundColor("#6366f1")
            .borderRadius(8)
            .onClick(() => this.retry())
        }
        .width("100%")
        .height("100%")
        .backgroundColor("#0f172a")
        .justifyContent(FlexAlign.Center)
      }
    }
    .width("100%")
    .height("100%")
  }
}
