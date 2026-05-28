# DevPulse（AI 潮汐）Phase 3 增量 PRD

> **版本范围**：0.2.1 → 0.3.0  
> **基线版本**：0.2.0（Win 桌面 Tauri + Android Capacitor 基础）  
> **文档版本**：v1.0  
> **语言**：中文  
> **编程语言**：Python 3.10+（后端 FastAPI）、TypeScript（前端 React 18）、ArkTS（鸿蒙容器）

---

## 一、项目信息

| 字段 | 内容 |
|------|------|
| **Project Name** | `devpulse` |
| **阶段代号** | Phase 3 — 跨三端产品化（云端部署 + 用户系统 + 鸿蒙） |
| **原始需求** | 将 DevPulse 从桌面/Android MVP 演进为 Win + Android + 鸿蒙三端完整产品，补齐云基础设施（后端部署、用户认证、多端同步）、扩展多数据源、接入鸿蒙生态并完成 AppGallery 上架 |
| **起点版本** | 0.2.0（桌面 Tauri 发布 + Capacitor 移动壳初始化 + APK 构建脚本就绪，后端运行在本地 PC） |
| **终点版本** | 0.3.0（鸿蒙 HAP 签名 + AppGallery 上架） |
| **总版本数** | 8 个小版本 |

---

## 二、产品定义

### 2.1 产品目标（Phase 3）

| # | 目标 | 衡量标准 |
|---|------|---------|
| G1 | **移动端独立可用**：Android 不依赖本地 PC 后端，通过云端 API 独立运行 | Android 真机切 4G → 首页数据正常加载 |
| G2 | **用户体系闭环**：注册/登录 + 跨设备收藏同步，用户数据不丢失 | 同一账号在 Win 桌面和 Android 端收藏列表一致 |
| G3 | **鸿蒙生态接入**：前端代码复用 + ArkUI WebView 容器，完成 AppGallery 上架 | AppGallery 搜索"AI 潮汐"可见并可下载 |

### 2.2 用户故事（按版本）

#### 0.2.1 — Android 真机验证

| # | 用户故事 |
|---|---------|
| US1 | As a **测试用户**, I want **USB 连接真机后能直接运行 APK 并看到 Trending 列表** so that **验证 Capacitor 构建链路在真实设备上可用** |
| US2 | As a **移动端用户**, I want **卡片列表可以用手指流畅滑动且按钮不小于 48px** so that **在手机屏幕上操作不会误触** |
| US3 | As a **开发者**, I want **Gradle 构建在 2 分钟内完成且无警告** so that **CI/CD 流水线能稳定产出 APK** |

#### 0.2.2 — 后端云部署

| # | 用户故事 |
|---|---------|
| US1 | As a **移动端用户**, I want **不连接 PC Wi-Fi 也能打开 App 看到 Trending 数据** so that **通勤路上、外出时也能使用** |
| US2 | As a **运维者**, I want **后端 Docker 镜像推送到 Render/Railway 后自动部署** so that **无需手动 SSH 操作服务器** |
| US3 | As a **开发者**, I want **SQLite 历史数据无缝迁移到 PostgreSQL** so that **已有周报数据不丢失** |

#### 0.2.3 — 用户系统 + 跨端同步

| # | 用户故事 |
|---|---------|
| US1 | As a **新用户**, I want **用邮箱和密码注册账号** so that **我的收藏数据可以跨设备同步** |
| US2 | As a **已登录用户**, I want **在 Win 桌面收藏的项目自动出现在 Android 端收藏列表** so that **换设备不用重新收藏** |
| US3 | As a **安全敏感用户**, I want **密码加密存储且登录 Token 有过期时间** so that **账号不会被盗用** |

#### 0.2.4 — 多源扩展

| # | 用户故事 |
|---|---------|
| US1 | As a **多语言开发者**, I want **按语言筛选 Trending 时能覆盖 Rust/Haskell/Elixir 等小众语言** so that **不只是看 Python/JS 热门项目** |
| US2 | As a **国内开发者**, I want **查看 Gitee 热门项目** so that **关注国内开源生态动态** |
| US3 | As a **全栈开发者**, I want **在 GitHub/GitLab/Gitee 三个数据源间一键切换** so that **一站式掌握全球开源趋势** |

#### 0.2.5 — 移动端推送

| # | 用户故事 |
|---|---------|
| US1 | As a **Android 用户**, I want **每周一 9:00 收到新周报推送通知** so that **不错过每周 AI 热门项目** |
| US2 | As a **推送偏好用户**, I want **在设置中关闭/开启推送通知** so that **不想被打扰时可以静默** |
| US3 | As a **通知点击用户**, I want **点击推送通知直接打开对应周报详情** so that **一键直达内容而非仅看到通知** |

#### 0.2.6 — 鸿蒙入门

| # | 用户故事 |
|---|---------|
| US1 | As a **鸿蒙开发者**, I want **DevEco Studio 项目能加载 WebView 并显示 Trending 列表** so that **验证前端代码在鸿蒙容器中可运行** |
| US2 | As a **项目维护者**, I want **harmony/ 目录结构清晰且与前端 dist/ 自动对接** so that **后续鸿蒙适配有明确入口** |
| US3 | As a **架构师**, I want **ArkUI Web 组件正确加载前端 SPA 路由** so that **所有页面（列表/详情/搜索/收藏）在鸿蒙中可访问** |

#### 0.2.7 — 鸿蒙 UI 适配

| # | 用户故事 |
|---|---------|
| US1 | As a **鸿蒙用户**, I want **收到新周报时系统通知栏弹出** so that **和 Android 端体验一致** |
| US2 | As a **鸿蒙用户**, I want **刘海屏区域不被内容遮挡且支持侧滑返回** so that **全面屏手机体验正常** |
| US3 | As a **鸿蒙用户**, I want **离线时仍能看到上次缓存的周报数据** so that **地铁通勤无网络也能浏览** |

#### 0.2.8 — QA + 商店准备

| # | 用户故事 |
|---|---------|
| US1 | As a **QA 工程师**, I want **Win/Android/鸿蒙三端回归测试矩阵覆盖所有核心功能** so that **发布前确认无回归 Bug** |
| US2 | As a **产品运营**, I want **AppGallery 上架所需的应用截图、描述文案、隐私政策齐全** so that **提交审核一次通过** |
| US3 | As a **无障碍用户**, I want **屏幕阅读器能正确朗读页面内容** so that **视障用户也能使用** |

#### 0.3.0 — 鸿蒙正式发布

| # | 用户故事 |
|---|---------|
| US1 | As a **鸿蒙手机用户**, I want **在 AppGallery 搜索'AI 潮汐'能找到并下载** so that **一键安装无需侧载** |
| US2 | As a **产品负责人**, I want **HAP 签名流程自动化（CI 产出签名包）** so that **后续版本更新效率高** |
| US3 | As a **早期鸿蒙用户**, I want **AppGallery 详情页描述清晰、截图真实** so that **下载前就知道 App 能做什么** |

---

## 三、技术规范

### 3.1 需求池（Phase 3 全局优先级）

#### P0 — 必须实现（阻塞发布）

| ID | 需求 | 所属版本 | 验收标准 |
|----|------|---------|---------|
| P0-1 | Android USB 真机运行，首页数据正常加载 | 0.2.1 | `npx cap open android` → USB 真机 → Trending 列表渲染 |
| P0-2 | 移动端触控最小触摸区域 ≥48px | 0.2.1 | 所有可点击元素宽高 ≥48px |
| P0-3 | Dockerfile + 云部署（Render/Railway） | 0.2.2 | `curl https://api.devpulse.app/health` → 200 |
| P0-4 | SQLite → PostgreSQL 数据迁移 | 0.2.2 | 历史周报数据在 PostgreSQL 中可查询 |
| P0-5 | 用户注册/登录（JWT + bcrypt） | 0.2.3 | 注册 → 登录 → 获取 Token → 访问受保护端点 |
| P0-6 | 收藏关联 user_id，跨设备同步 | 0.2.3 | 设备 A 收藏 → 设备 B 登录同账号 → 收藏列表一致 |
| P0-7 | 前端 AuthPage（登录/注册表单） | 0.2.3 | 表单验证 + Token localStorage 持久化 + 401 自动跳转登录 |
| P0-8 | DevEco Studio 项目初始化 + WebView 加载 dist/ | 0.2.6 | 模拟器展示 Trending 列表 |
| P0-9 | HAP 签名打包 + AppGallery Connect 上传 | 0.3.0 | AppGallery 审核通过 |

#### P1 — 应该实现（影响体验）

| ID | 需求 | 所属版本 | 验收标准 |
|----|------|---------|---------|
| P1-1 | Gradle 构建时间 <2 分钟 | 0.2.1 | 增量构建 <2min，clean 构建 <5min |
| P1-2 | 健康检查 + 容器自动重启策略 | 0.2.2 | `docker-compose` 中 `restart: unless-stopped` |
| P1-3 | `TrendingSource` 抽象基类 → GitHubSource | 0.2.4 | 新增数据源只需继承基类实现 `fetch_trending()` |
| P1-4 | 前端数据源 Tab 切换（GitHub / GitLab / Gitee） | 0.2.4 | Tab 切换 → API 请求不同数据源 → 列表更新 |
| P1-5 | FCM 集成 + Capacitor push-notifications 插件 | 0.2.5 | 后端触发 → FCM → Android 通知栏弹出 |
| P1-6 | 推送偏好云同步到 users 表 | 0.2.5 | Web 端修改偏好 → Android 端生效 |
| P1-7 | 鸿蒙 @ohos.notification 原生通知 | 0.2.7 | 周报生成 → 鸿蒙通知栏弹出 |
| P1-8 | 鸿蒙 safe-area 刘海屏适配 | 0.2.7 | 内容不被刘海/挖孔遮挡 |
| P1-9 | 鸿蒙侧滑返回手势 | 0.2.7 | 左滑/右滑 → 返回上一页 |
| P1-10 | 三端回归测试矩阵（Win/Android/鸿蒙） | 0.2.8 | 核心功能测试通过率 >95% |
| P1-11 | AppGallery 上架材料（截图 + 描述 + 隐私政策） | 0.2.8 | 材料齐全，格式符合 AppGallery 规范 |

#### P2 — 可以实现（锦上添花）

| ID | 需求 | 所属版本 | 验收标准 |
|----|------|---------|---------|
| P2-1 | 移动端下拉刷新 + 上拉加载更多 | 0.2.1 | 手势触发刷新/分页 |
| P2-2 | CDN 静态资源加速 | 0.2.2 | 首屏加载时间减少 30% |
| P2-3 | GitLab Source 数据源实现 | 0.2.4 | GitLab Trending 页面数据可抓取 |
| P2-4 | Gitee Source 数据源实现 | 0.2.4 | Gitee 热门项目数据可抓取 |
| P2-5 | 语言筛选器扩展至 20+ 选项 | 0.2.4 | 前端语言下拉列表 ≥20 个选项 |
| P2-6 | 鸿蒙 @ohos.data.preferences 本地缓存 | 0.2.7 | 离线打开 → 展示上次缓存数据 |
| P2-7 | 性能基线（首屏 <2s） | 0.2.8 | Lighthouse 首屏 <2s |
| P2-8 | 无障碍适配（屏幕阅读器） | 0.2.8 | TalkBack / 鸿蒙屏幕朗读可正常使用 |

### 3.2 UI 设计概要

#### 新增/变更页面

| 页面 | 版本 | 说明 |
|------|------|------|
| **AuthPage**（新增） | 0.2.3 | 登录/注册双 Tab 表单。邮箱 + 密码 + 确认密码（注册）；"记住我"复选框；错误状态提示（邮箱格式/密码长度/账号不存在/密码错误） |
| **数据源切换 Tab**（变更） | 0.2.4 | Trending 列表顶部新增 3 个 Tab：GitHub / GitLab / Gitee；默认 GitHub；切换时列表刷新 |
| **语言筛选器扩展**（变更） | 0.2.4 | 从现有少数语言扩展到 20+ 选项的下拉多选菜单 |
| **推送偏好设置**（新增） | 0.2.5 | 设置页新增开关：周报推送（默认开）、重要项目推送（默认关）；云同步状态标识 |
| **鸿蒙标题栏**（新增） | 0.2.7 | ArkUI 原生标题栏（替代 Web 内标题栏），含返回按钮 + 页面标题 + 右侧菜单 |

#### 三端 UI 复用原则

```
shared/components/   ← 所有 UI 组件（React），三端共用
desktop/src/         ← Tauri 桌面壳引用 shared/
mobile/              ← Capacitor 壳引用 shared/，仅 capacitor.config.ts 差异
harmony/webview/     ← ArkUI Web 组件加载 shared/ 构建产物 dist/，不做独立 UI
```

- **不对鸿蒙单独写一套 UI**：鸿蒙端通过 WebView 加载与桌面/移动端相同的 React SPA 产物
- 鸿蒙端仅处理**容器级适配**：标题栏、通知、刘海屏 safe-area、手势返回、本地存储（通过 `@ohos` API 桥接）

### 3.3 关键技术决策

| 决策 | 选型 | 理由 |
|------|------|------|
| 云平台 | Render.com (Web Service) 或 Railway | 免费 tier 512MB RAM，Git 集成自动部署，SSL 自动 |
| 数据库 | Supabase PostgreSQL（免费 500MB）或 Neon | 免费额度够用（每周 25 条记录），支持 JWT RLS |
| 用户认证 | PyJWT + bcrypt（自建） | 不做 OAuth，减少三方依赖 |
| 移动推送 | Firebase Cloud Messaging | Android 原生支持，Capacitor 插件成熟，免费 |
| LLM 成本 | DeepSeek 优先 | 约 ¥0.02/次摘要，远低于 GPT-4 |
| 鸿蒙容器 | ArkUI Web 组件 | 复用现有 React 前端，不重写 UI |
| 鸿蒙存储 | @ohos.data.preferences | 原生 KV 存储，替代 IndexedDB（鸿蒙 WebView 不完全支持） |

### 3.4 新增 API 端点

| Method | Endpoint | 版本 | 说明 |
|--------|----------|------|------|
| POST | `/api/v1/auth/register` | 0.2.3 | 注册（email + password → JWT） |
| POST | `/api/v1/auth/login` | 0.2.3 | 登录（email + password → JWT） |
| GET | `/api/v1/auth/me` | 0.2.3 | 获取当前用户信息（需 Bearer Token） |
| GET | `/api/v1/trending?source=gitlab` | 0.2.4 | 按数据源筛选 |
| GET | `/api/v1/languages` | 0.2.4 | 获取支持的语言列表 |
| PUT | `/api/v1/user/preferences` | 0.2.5 | 更新推送偏好 |
| GET | `/api/v1/health` | 0.2.2 | 健康检查（返回 DB 连接状态 + 最近周报时间） |

### 3.5 关键约束复述

| 约束 | 落实方式 |
|------|---------|
| 云部署免费 tier | Render 512MB 或 Railway $5 credit；Supabase/Neon 免费 500MB PostgreSQL |
| 前端三端复用 | 鸿蒙不使用独立 UI，通过 ArkUI Web 组件加载 shared/ 产物 |
| 自建认证 | PyJWT Token（access 24h + refresh 7d），bcrypt 密码哈希 |
| LLM 成本控制 | DeepSeek 优先（¥0.002/1K tokens ≈ ¥0.02/次），失败时 fallback Qwen |

---

## 四、Open Questions（待确认）

| # | 问题 | 影响范围 | 建议 |
|---|------|---------|------|
| Q1 | Render.com 免费 tier 冷启动延迟 30-50s，是否需要预热方案？ | 0.2.2 | 建议前端首次请求展示 skeleton loading + 30s 超时 |
| Q2 | Supabase PostgreSQL 免费 500MB 够用多久？按每周 25 条 repo + 摘要（约 50KB/条），约够 10,000 周 ≈ 192 年 | 0.2.2 | 风险极低，但建议 0.2.2 加一个 DB 行数监控 |
| Q3 | FCM 是否需要国内推送通道（华为 HMS Push）替代方案？ | 0.2.5 | 国外用户 FCM 直接可用，国内 Android 用户可能收不到。建议 P2 预留 HMS 适配 |
| Q4 | 鸿蒙 NEXT（纯血）是否完全支持 Web 组件？已知部分 CSS 特性有差异 | 0.2.6 | 建议 0.2.6 做 Web 组件兼容性测试矩阵，记录不兼容 CSS/JS API |
| Q5 | Gitee API 是否需要 OAuth 授权？已知未授权 API 速率限制严格（100次/天） | 0.2.4 | 建议先做无需授权的公开 Trending 页面解析（同 GitHub 方案），API 补全作为 P2 |
| Q6 | 鸿蒙 AppGallery 审核周期通常多久？是否需要提前 2 周提交？ | 0.3.0 | 建议 0.2.8 启动时同步提交审核草稿 |
| Q7 | 用户密码强度要求：最小长度？是否要求大小写+数字+特殊字符？ | 0.2.3 | 建议最小 8 位 + 至少包含字母和数字 |

---

## 五、里程碑与交付节奏

```
0.2.1 ████████░░░░░░░░░░░░░░ 第 1 周  │ Android 真机验证
0.2.2 ░░░░░░░░████████░░░░░░ 第 2 周  │ 后端云部署      ┐
0.2.3 ░░░░░░░░░░░░░░████████ 第 3 周  │ 用户系统        ├─ 云基础设施闭环
0.2.4 ░░░░░░░░░░░░░░████████ 第 3 周  │ 多源扩展        │  (可与鸿蒙并行)
0.2.5 ░░░░░░░░░░░░░░░░░░████ 第 4 周  │ 移动推送        ┘
0.2.6 ░░░░░░░░░░░░░░████████ 第 3 周  │ 鸿蒙入门        ┐
0.2.7 ░░░░░░░░░░░░░░░░░░████ 第 4 周  │ 鸿蒙 UI 适配    ├─ 鸿蒙生态闭环
0.2.8 ░░░░░░░░░░░░░░░░░░░░██ 第 5 周  │ QA + 商店准备   │
0.3.0 ░░░░░░░░░░░░░░░░░░░░░█ 第 6 周  │ 鸿蒙发布        ┘
```

> **并行策略**：0.2.3/0.2.4/0.2.5（云基础设施）与 0.2.6/0.2.7（鸿蒙生态）可并行推进。总工期约 4-6 周。

---

## 六、风险登记

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Render 免费 tier 被取消或缩水 | 低 | 高 | Railway / Fly.io 作为备选，一键切换 Docker 部署 |
| 鸿蒙 Web 组件不兼容前端某些 JS API | 中 | 中 | 0.2.6 先做兼容性摸底，必要时前端 polyfill |
| AppGallery 审核不通过 | 中 | 高 | 0.2.8 提前准备合规材料，参考同类应用审核经验 |
| DeepSeek API 不稳定 | 中 | 低 | 保留 Qwen/Claude fallback 链路（已有 4 厂商适配器） |
| PostgreSQL 迁移数据丢失 | 低 | 高 | 迁移前备份 SQLite 文件，迁移脚本含校验步骤 |
