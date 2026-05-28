/**
 * DevPulse 鸿蒙原生标题栏
 *
 * 替代 Web 内标题栏（鸿蒙模式下 Layout.tsx 隐藏 Web 导航栏），
 * 提供原生返回按钮 + 标题 + 右侧菜单。
 */

import { router } from "@kit.ArkUI";

@Component
export struct TitleBar {
  /** 页面标题 */
  @Prop title: string = "DevPulse";

  /** 是否显示返回按钮 */
  @Prop showBack: boolean = false;

  /** 返回回调（默认 router.back） */
  onBack?: () => void;

  build() {
    Row() {
      // ── 返回按钮 ──────────────────────────
      if (this.showBack) {
        Button() {
          Image($r("sys.media.ohos_ic_public_arrow_left"))
            .width(24)
            .height(24)
            .fillColor("#e2e8f0")
        }
        .type(ButtonType.Circle)
        .width(40)
        .height(40)
        .backgroundColor("#1e293b")
        .onClick(() => {
          if (this.onBack) {
            this.onBack();
          } else {
            router.back();
          }
        })
        .margin({ right: 12 })
      }

      // ── 标题 ──────────────────────────────
      Text(this.title)
        .fontSize(18)
        .fontWeight(FontWeight.Bold)
        .fontColor("#ffffff")
        .layoutWeight(1)
        .maxLines(1)
        .textOverflow({ overflow: TextOverflow.Ellipsis })

      // ── 右侧菜单（预留）────────────────────
      // 可扩展：搜索图标、更多菜单等
    }
    .width("100%")
    .height(56)
    .padding({ left: 16, right: 16 })
    .backgroundColor("#0f172a") // slate-900
    .border({
      width: { bottom: 1 },
      color: "#1e293b", // slate-800
    })
  }
}
