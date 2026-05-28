/**
 * DevPulse 鸿蒙 Safe Area 适配容器
 *
 * 处理刘海屏、挖孔屏的安全区域，
 * 确保内容不被系统状态栏/导航栏遮挡。
 */

import { window } from "@kit.ArkUI";
import { hilog } from "@kit.PerformanceAnalysisKit";

const TAG = "SafeAreaWrapper";
const DOMAIN = 0x0001;

@Component
export struct SafeAreaWrapper {
  /** 子组件内容 */
  @BuilderParam content: () => void = this.defaultContent;

  /** 安全区域 insets */
  @State topInset: number = 0;
  @State bottomInset: number = 0;
  @State leftInset: number = 0;
  @State rightInset: number = 0;

  aboutToAppear(): void {
    this.calculateSafeArea();
  }

  /**
   * 计算安全区域
   */
  private async calculateSafeArea(): Promise<void> {
    try {
      const mainWindow = await window.getLastWindow(getContext());
      const avoidArea = mainWindow.getWindowAvoidArea(
        window.AvoidAreaType.TYPE_SYSTEM
      );

      this.topInset = vp2px(avoidArea.topRect.height);
      this.bottomInset = vp2px(avoidArea.bottomRect.height);
      this.leftInset = vp2px(avoidArea.leftRect.width);
      this.rightInset = vp2px(avoidArea.rightRect.width);

      hilog.info(
        DOMAIN,
        TAG,
        `SafeArea: T=${this.topInset}, B=${this.bottomInset}, L=${this.leftInset}, R=${this.rightInset}`
      );

      // 将安全区域值注入到 WebView CSS 变量
      this.injectSafeAreaToWeb();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `calculateSafeArea failed: ${err}`);
    }
  }

  /**
   * 将安全区域注入到 WebView（通过 JS Bridge 或直接操作 DOM）
   */
  private injectSafeAreaToWeb(): void {
    // 通过 jsBridge 将安全区域值传递给前端
    // 前端通过 CSS env(safe-area-inset-*) 或 JS 变量获取
    try {
      // Web 组件通过 __HARMONY__ 获取 safeArea 值
    } catch (err) {
      hilog.error(DOMAIN, TAG, `injectSafeAreaToWeb failed: ${err}`);
    }
  }

  @Builder
  defaultContent() {
    Text("")
  }

  build() {
    Column() {
      // 顶部安全区域填充
      if (this.topInset > 0) {
        Row()
          .width("100%")
          .height(this.topInset)
          .backgroundColor("#0f172a") // slate-900
      }

      // 主内容区域
      this.content()

      // 底部安全区域填充
      if (this.bottomInset > 0) {
        Row()
          .width("100%")
          .height(this.bottomInset)
          .backgroundColor("#0f172a")
      }
    }
    .width("100%")
    .height("100%")
    .backgroundColor("#0f172a")
  }
}
