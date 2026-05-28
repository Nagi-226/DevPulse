# DevPulse Phase 3 系统架构设计

> **版本范围**：0.2.1 → 0.3.0  
> **架构师**：Bob（高见远）  
> **文档版本**：v1.0  
> **日期**：2026-05-28  

---

## Part A: 系统设计

---

### 1. 实现方案

#### 1.1 核心挑战与选型

| 挑战 | 选型 | 理由 |
|------|------|------|
| **SQLite → PostgreSQL 迁移** | Alembic + 自定义导出脚本 | Alembic 是 SQLAlchemy 生态标准迁移工具；导出脚本处理 SQLite 特殊类型（JSON→JSONB） |
| **JWT 认证** | PyJWT（HS256）+ bcrypt（passlib） | 自建认证无三方依赖；bcrypt 是 NIST 推荐密码哈希算法；HS256 对称密钥简单可靠 |
| **Docker 部署** | 多阶段 Dockerfile + docker-compose | Python slim 基础镜像（~150MB）；docker-compose 编排 app + db 双服务 |
| **云 PostgreSQL** | Supabase PostgreSQL（免费 500MB） | 免费额度远超需求；内置连接池 PgBouncer；Supabase JS 客户端可选 |
| **FCM 推送** | firebase-admin SDK + @capacitor/push-notifications | Google 官方库，REST API 调用；Capacitor 插件封装原生 FCM SDK |
| **鸿蒙容器** | ArkUI Web 组件 + JS Bridge | 复用 React SPA 产物，零前端重写；Bridge 暴露 @ohos API 给 Web 环境 |
| **多数据源** | TrendingSource 抽象基类（策略模式） | 新增数据源只需继承基类；GitHub/GitLab/Gitee 共用爬虫基础设施 |

#### 1.2 架构模式

```
Phase 3 架构分层（增量）：

┌─────────────────────────────────────────────────┐
│  前端 (React 18 SPA)                             │
│  ├─ AuthPage (NEW)      ├─ 数据源Tab (MODIFY)    │
│  ├─ 推送偏好 (NEW)       ├─ 鸿蒙safe-area (NEW)   │
│  └─ 离线缓存 (ENHANCE)                          │
├─────────────────────────────────────────────────┤
│  API 网关层                                       │
│  ├─ /auth/* (NEW)       ├─ JWT 中间件 (NEW)      │
│  ├─ /trending?source=   ├─ /user/preferences     │
│  └─ /health (ENHANCE)                           │
├─────────────────────────────────────────────────┤
│  业务服务层                                       │
│  ├─ AuthService (NEW)   ├─ FCMService (NEW)      │
│  ├─ TrendingSource (NEW)├─ GitHubSource (REFACTOR)│
│  └─ GitLabSource/GiteeSource (NEW)              │
├─────────────────────────────────────────────────┤
│  数据持久层                                       │
│  ├─ PostgreSQL (NEW)    ├─ Alembic Migrations    │
│  └─ SQLite → PG 导出脚本                         │
├─────────────────────────────────────────────────┤
│  平台适配层                                       │
│  ├─ Capacitor (MODIFY)  ├─ ArkUI WebView (NEW)  │
│  └─ @ohos.* Bridge (NEW)                        │
└─────────────────────────────────────────────────┘
```

---

### 2. 文件列表

> 标注：🆕 NEW = 新建文件 | ✏️ MODIFY = 修改现有文件 | 📋 REF = 仅需查阅

#### 0.2.1 — Android 真机验证

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `mobile/android/app/build.gradle` | ✏️ | Gradle 构建参数调优（增量构建 <2min） |
| `mobile/capacitor.config.ts` | ✏️ | webDir 路径修正、server.url 配置 |
| `desktop/src/index.css` | ✏️ | 移动端触控适配：最小触摸区域 48px、滚动优化 |
| `desktop/src/components/TrendingList.tsx` | ✏️ | 移动端下拉刷新 + 上拉加载更多 |
| `desktop/src/components/RepoTrendingCard.tsx` | ✏️ | 卡片最小高度适配 48px 触控区域 |

#### 0.2.2 — 后端云部署

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `backend/Dockerfile` | 🆕 | 多阶段构建（Python 3.11-slim） |
| `backend/docker-compose.yml` | 🆕 | app + postgres 双服务编排 |
| `backend/.dockerignore` | 🆕 | Docker 构建排除规则 |
| `backend/alembic.ini` | 🆕 | Alembic 迁移配置 |
| `backend/migrations/env.py` | 🆕 | Alembic 环境配置（async SQLAlchemy） |
| `backend/migrations/versions/001_add_users_table.py` | 🆕 | 首版迁移脚本 |
| `backend/scripts/export_sqlite_to_pg.py` | 🆕 | SQLite → PostgreSQL 数据导出 |
| `backend/devpulse/config.py` | ✏️ | 新增 DATABASE_URL（PG）、RENDER、FCM 等环境变量 |
| `backend/devpulse/core/database.py` | ✏️ | 支持 PostgreSQL 连接串（asyncpg） |
| `backend/devpulse/main.py` | ✏️ | 新增 `/health` 增强（DB 状态 + 最近周报时间）；lifespan 中运行迁移 |
| `desktop/src/utils/api-client.ts` | ✏️ | API_BASE_URL 优先级：`VITE_API_BASE` 环境变量 > Tauri localhost > Vite proxy |

#### 0.2.3 — 用户系统 + 跨端同步

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `backend/devpulse/core/models.py` | ✏️ | 新增 `User` 模型；`Favorite` 关联 user_id 改为非 default |
| `backend/devpulse/api/endpoints/auth.py` | 🆕 | `/auth/register`、`/auth/login`、`/auth/me` 端点 |
| `backend/devpulse/api/dependencies.py` | 🆕 | `get_current_user` JWT 依赖注入 |
| `backend/devpulse/services/auth_service.py` | 🆕 | 密码哈希（bcrypt）、JWT 签发/验证、refresh token |
| `backend/devpulse/api/endpoints/repos.py` | ✏️ | 收藏端点关联 user_id（从 JWT 解析） |
| `desktop/src/pages/AuthPage.tsx` | 🆕 | 登录/注册双 Tab 表单；邮箱+密码+确认密码（注册）；"记住我" |
| `desktop/src/components/ProtectedRoute.tsx` | 🆕 | 路由守卫：未登录跳转 AuthPage |
| `desktop/src/stores/useAuthStore.ts` | 🆕 | Zustand：user/token/refresh/logout |
| `desktop/src/utils/api-client.ts` | ✏️ | 请求自动携带 `Authorization: Bearer <token>`；401 → refresh → 重试 |
| `desktop/src/types/index.ts` | ✏️ | 新增 `User`、`AuthResponse`、`LoginRequest`、`RegisterRequest` 类型 |
| `desktop/src/App.tsx` | ✏️ | 新增 `/auth` 路由；AuthPage 不套 Layout |

#### 0.2.4 — 多源扩展

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `backend/devpulse/services/trending_source.py` | 🆕 | `TrendingSource` 抽象基类 + `GitHubSource` / `GitLabSource` / `GiteeSource` |
| `backend/devpulse/services/trending_scraper.py` | ✏️ | 重构为调用 `TrendingSource` 工厂方法 |
| `backend/devpulse/api/endpoints/repos.py` | ✏️ | `/trending` 新增 `source` 参数；新增 `/languages` 端点 |
| `desktop/src/components/DataSourceTabs.tsx` | 🆕 | GitHub / GitLab / Gitee 三 Tab 切换组件 |
| `desktop/src/components/LanguageFilter.tsx` | 🆕 | 20+ 语言多选下拉菜单 |
| `desktop/src/pages/TrendingPage.tsx` | ✏️ | 集成 DataSourceTabs + LanguageFilter |
| `desktop/src/stores/useTrendingStore.ts` | ✏️ | 新增 `source`、`language` 筛选参数 |
| `desktop/src/types/index.ts` | ✏️ | 新增 `TrendingSource` 枚举、`LanguageOption` 类型 |

#### 0.2.5 — 移动端推送

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `backend/devpulse/services/fcm_service.py` | 🆕 | Firebase Admin SDK 集成：注册 Token、广播推送 |
| `backend/devpulse/api/endpoints/auth.py` | ✏️ | 新增 `PUT /user/fcm-token` 端点 |
| `backend/devpulse/api/endpoints/repos.py` | ✏️ | 新增 `PUT /user/preferences` 端点 |
| `backend/devpulse/services/scheduler.py` | ✏️ | 周报生成后触发 FCM 广播 |
| `backend/devpulse/config.py` | ✏️ | 新增 `FCM_CREDENTIALS_PATH` 环境变量 |
| `mobile/package.json` | ✏️ | 新增 `@capacitor/push-notifications` 依赖 |
| `mobile/capacitor.config.ts` | ✏️ | 新增 `PushNotifications` 插件声明 |
| `desktop/src/pages/SettingsPage.tsx` | ✏️ | 新增推送偏好开关（周报推送/重要项目推送） |
| `desktop/src/stores/useNotificationStore.ts` | ✏️ | 新增 `fcmToken` 管理、偏好同步至后端 |

#### 0.2.6 — 鸿蒙入门

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `harmony/build-profile.json5` | 🆕 | DevEco Studio 项目构建配置 |
| `harmony/entry/src/main/module.json5` | 🆕 | 模块声明（权限：INTERNET、NOTIFICATION） |
| `harmony/entry/src/main/ets/pages/Index.ets` | 🆕 | ArkUI 入口页：Web 组件加载 `dist/index.html` |
| `harmony/entry/src/main/ets/webview/WebViewContainer.ets` | 🆕 | WebView 容器封装：JS Bridge、路由拦截、加载状态 |
| `harmony/entry/src/main/ets/bridge/JsBridge.ets` | 🆕 | JS ↔ ArkTS 双向通信桥（通知、存储、设备信息） |
| `harmony/entry/src/main/resources/base/element/string.json` | 🆕 | 鸿蒙字符串资源 |
| `harmony/hvigor/hvigor-config.json5` | 🆕 | Hvigor 构建配置 |
| `scripts/build_harmony_webview.sh` | 🆕 | 构建前端 dist/ → 复制到 harmony/webview/ |

#### 0.2.7 — 鸿蒙 UI 适配

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `harmony/entry/src/main/ets/notification/NotificationService.ets` | 🆕 | @ohos.notification 原生通知服务 |
| `harmony/entry/src/main/ets/pages/SafeAreaWrapper.ets` | 🆕 | 刘海屏 safe-area 适配容器 |
| `harmony/entry/src/main/ets/pages/TitleBar.ets` | 🆕 | ArkUI 原生标题栏（替代 Web 内标题栏） |
| `harmony/entry/src/main/ets/storage/PreferencesStore.ets` | 🆕 | @ohos.data.preferences 本地缓存封装 |
| `desktop/src/index.css` | ✏️ | 鸿蒙 safe-area CSS 变量：`env(safe-area-inset-*)` |
| `desktop/src/components/Layout.tsx` | ✏️ | 鸿蒙模式下隐藏 Web 内导航栏（由原生 TitleBar 接管） |
| `harmony/entry/src/main/ets/entryability/EntryAbility.ets` | ✏️ | 生命周期注册：通知权限请求、手势返回拦截 |

#### 0.2.8 — QA + 商店准备

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `docs/test_matrix_phase3.md` | 🆕 | 三端（Win/Android/鸿蒙）回归测试矩阵 |
| `docs/privacy_policy.md` | 🆕 | 隐私政策（中文） |
| `docs/appgallery_listing.md` | 🆕 | AppGallery 上架文案（标题/描述/关键词） |
| `docs/screenshots/` | 🆕 | 三端应用截图（按 AppGallery 规格） |
| `desktop/src/pages/PrivacyPage.tsx` | 🆕 | 隐私政策展示页（App 内可查看） |
| `desktop/src/App.tsx` | ✏️ | 新增 `/privacy` 路由 |
| `desktop/src/components/AccessibilityWrapper.tsx` | 🆕 | 无障碍增强：aria-label、role、语义化 HTML |

#### 0.3.0 — 鸿蒙发布

| 文件路径 | 操作 | 说明 |
|---------|:----:|------|
| `harmony/entry/src/main/resources/base/profile/agconnect-services.json` | 🆕 | AppGallery Connect 配置文件 |
| `harmony/build-profile.json5` | ✏️ | 签名配置（debug/release 证书指纹） |
| `scripts/sign_hap.sh` | 🆕 | HAP 签名打包脚本（CI 自动化） |
| `scripts/upload_appgallery.sh` | 🆕 | AppGallery Connect API 上传脚本 |
| `docs/release_notes_0.3.0.md` | 🆕 | 0.3.0 发布说明 |

---

### 3. 数据结构与接口

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str password_hash
        +str display_name
        +bool push_enabled
        +bool push_weekly_report
        +bool push_important_project
        +str fcm_token
        +datetime created_at
        +datetime updated_at
    }

    class Repository {
        +int id
        +str full_name
        +str owner
        +str name
        +str description
        +str language
        +list topics
        +int total_stars
        +int stars_since
        +int forks
        +int forks_since
        +int open_issues
        +datetime created_at
        +datetime updated_at
        +str url
        +bool has_readme
        +str readme_content
        +str readme_summary
        +list key_points
        +list tags
        +datetime crawled_at
        +datetime summarized_at
        +int trending_rank
        +str trending_since
        +str source
    }

    class WeeklyReport {
        +int id
        +datetime week_start
        +datetime week_end
        +str language_filter
        +str source_filter
        +int total_repos
        +list top_repos
        +str overview_text
        +datetime generated_at
        +bool published
        +datetime published_at
    }

    class Favorite {
        +int id
        +int user_id
        +int repo_id
        +datetime created_at
    }

    class StarHistory {
        +int id
        +int repo_id
        +int total_stars
        +datetime recorded_at
    }

    class AuthRequest {
        +str email
        +str password
    }

    class RegisterRequest {
        +str email
        +str password
        +str confirm_password
        +str display_name
    }

    class AuthResponse {
        +str access_token
        +str refresh_token
        +str token_type
        +int expires_in
        +User user
    }

    class TokenPayload {
        +int sub
        +str email
        +int exp
        +int iat
        +str type
    }

    class TrendingSource {
        <<abstract>>
        +str source_name
        +fetch_trending(language, since, limit) list~TrendingRepo~
        +fetch_repo_detail(owner, repo) dict
    }

    class GitHubSource {
        +str source_name = "github"
        +fetch_trending(language, since, limit) list~TrendingRepo~
        +fetch_repo_detail(owner, repo) dict
    }

    class GitLabSource {
        +str source_name = "gitlab"
        +fetch_trending(language, since, limit) list~TrendingRepo~
        +fetch_repo_detail(owner, repo) dict
    }

    class GiteeSource {
        +str source_name = "gitee"
        +fetch_trending(language, since, limit) list~TrendingRepo~
        +fetch_repo_detail(owner, repo) dict
    }

    class AuthService {
        +hash_password(password) str
        +verify_password(plain, hashed) bool
        +create_access_token(user_id, email) str
        +create_refresh_token(user_id) str
        +decode_token(token) TokenPayload
    }

    class FCMService {
        +send_weekly_report_notification(report_id) int
        +send_to_user(user_id, title, body) bool
        +register_token(user_id, fcm_token) None
    }

    class TrendingRepo {
        +str full_name
        +str owner
        +str name
        +str description
        +str language
        +int total_stars
        +int stars_since
        +int forks
        +str url
    }

    class HealthResponse {
        +str status
        +str version
        +str db_status
        +datetime last_weekly_report
    }

    class PushPreferences {
        +bool enabled
        +bool weekly_report
        +bool important_project
    }

    User "1" --> "*" Favorite : has
    Repository "1" --> "*" Favorite : referenced_by
    Repository "1" --> "*" StarHistory : has_history
    TrendingSource <|-- GitHubSource : implements
    TrendingSource <|-- GitLabSource : implements
    TrendingSource <|-- GiteeSource : implements
    TrendingSource --> TrendingRepo : returns
    AuthService --> TokenPayload : creates
    AuthService --> User : manages
    FCMService --> User : sends_to
    AuthRequest --> AuthResponse : produces
    RegisterRequest --> AuthResponse : produces
    User --> PushPreferences : has
```

---

### 4. 程序调用流程

#### 4.1 用户注册 → 登录 → 收藏同步

```mermaid
sequenceDiagram
    participant Client as React SPA
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Auth as AuthService

    Note over Client,Auth: === 用户注册 ===
    Client->>API: POST /api/v1/auth/register<br/>{email, password, confirm_password}
    API->>Auth: 校验邮箱格式 + 密码强度（≥8位 + 字母+数字）
    API->>DB: SELECT id FROM users WHERE email=?
    DB-->>API: 不存在（OK）
    API->>Auth: hash_password(plain_password)
    Auth-->>API: bcrypt_hash
    API->>DB: INSERT INTO users (email, password_hash, ...)
    DB-->>API: user_id
    API->>Auth: create_access_token(user_id, email) + create_refresh_token(user_id)
    Auth-->>API: access_token (24h) + refresh_token (7d)
    API-->>Client: {access_token, refresh_token, user}

    Note over Client,Auth: === 用户登录 ===
    Client->>API: POST /api/v1/auth/login<br/>{email, password}
    API->>DB: SELECT * FROM users WHERE email=?
    DB-->>API: user record
    API->>Auth: verify_password(plain, hashed)
    Auth-->>API: True
    API->>Auth: create_access_token + create_refresh_token
    API-->>Client: {access_token, refresh_token, user}

    Note over Client,Auth: === 跨设备收藏同步 ===
    Note over Client: 设备A: 已登录，收藏项目
    Client->>API: POST /repos/{owner}/{repo}/star<br/>Authorization: Bearer <token>
    API->>API: decode_token → user_id
    API->>DB: INSERT INTO favorites (user_id, repo_id)
    DB-->>API: OK
    API-->>Client: {message: "Starred successfully"}

    Note over Client: 设备B: 登录同一账号
    Client->>API: GET /repos/collections<br/>Authorization: Bearer <token>
    API->>API: decode_token → user_id
    API->>DB: SELECT * FROM favorites JOIN repositories<br/>WHERE user_id=?
    DB-->>API: favorites list
    API-->>Client: {items: [...same as device A...]}
```

#### 4.2 云部署请求链路

```mermaid
sequenceDiagram
    participant Mobile as Android (4G)
    participant DNS as DNS
    participant Render as Render.com
    participant Docker as Docker Container
    participant PG as Supabase PostgreSQL

    Mobile->>DNS: api.devpulse.app
    DNS-->>Mobile: Render IP (SSL cert auto)
    Mobile->>Render: GET /api/v1/health
    Render->>Docker: Reverse proxy → :8000
    Docker->>PG: SELECT 1 (connection check)
    PG-->>Docker: OK
    Docker-->>Render: {status: "ok", db_status: "connected"}
    Render-->>Mobile: 200 OK (SSL encrypted)

    Mobile->>Render: GET /api/v1/trending?source=github&since=weekly
    Render->>Docker: Proxy request
    Docker->>PG: SELECT * FROM repositories<br/>WHERE trending_since='weekly'<br/>ORDER BY trending_rank LIMIT 25
    PG-->>Docker: 25 rows
    Docker-->>Render: JSON response
    Render-->>Mobile: {items: [...], total: 25}
```

#### 4.3 爬虫 → LLM → FCM 推送

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant Crawler as TrendingSource
    participant LLM as DeepSeek API
    participant DB as PostgreSQL
    participant FCM as FCM Service
    participant Device as Android Device

    Note over Scheduler: 每周一 9:00 UTC+8 触发
    Scheduler->>Crawler: fetch_trending(language="", since="weekly")
    Crawler->>Crawler: GitHubSource.fetch_trending()
    Crawler-->>Scheduler: 25 trending repos

    loop 每个仓库
        Scheduler->>DB: UPSERT INTO repositories
        DB-->>Scheduler: repo_id
        Scheduler->>LLM: POST /chat/completions<br/>{prompt: "生成中文摘要", repo: {...}}
        LLM-->>Scheduler: {summary, key_points, tags}
        Scheduler->>DB: UPDATE repositories SET readme_summary=?, ...
    end

    Scheduler->>DB: INSERT INTO weekly_reports
    DB-->>Scheduler: report_id

    Note over Scheduler,FCM: 推送通知
    Scheduler->>FCM: send_weekly_report_notification(report_id)
    FCM->>DB: SELECT fcm_token FROM users<br/>WHERE push_enabled=true AND push_weekly_report=true
    DB-->>FCM: [token1, token2, ...]
    FCM->>FCM: Firebase Admin SDK multicast
    FCM->>Device: FCM Push (via Google servers)
    Device->>Device: 通知栏弹出 "新周报已生成"
```

---

### 5. 待明确事项（Open Questions 建议）

#### PRD 中 7 个 Open Questions 的建议方案

| # | 问题 | 建议方案 | 理由 |
|---|------|---------|------|
| **Q1** | Render 冷启动 30-50s | 前端展示 skeleton loading + 30s 超时，VITE_API_BASE 可配置预热 ping（UptimeRobot 免费监控每 5 分钟 ping 一次） | UptimeRobot 免费方案可防止冷休眠；skeleton 改善用户感知 |
| **Q2** | Supabase 500MB 够用多久 | 采纳 PRD 分析（够 192 年），0.2.2 在 `/health` 端点中返回 DB 行数统计，dashboard 可选 | 风险极低；监控即可，无需主动扩容 |
| **Q3** | FCM 国内不可用 | **先不做 HMS**。国内 Android 用户通过 Tauri 桌面端获取通知；鸿蒙端走 @ohos.notification。未来 P2 考虑 HMS Push Kit | 0.2.5 聚焦海外 Android 用户；国内用户以桌面+鸿蒙为主 |
| **Q4** | 鸿蒙 Web 组件兼容性 | 0.2.6 建立兼容性检查清单：`fetch()`/`localStorage`/`IndexedDB`/CSS Grid/Flexbox/`position:fixed`。不兼容项记录到 `docs/harmony_webview_compat.md` | 提前摸底降低风险；必要时通过 JsBridge 注入 polyfill |
| **Q5** | Gitee API OAuth | **先做公开页面解析**（同 GitHub 方案）。Gitee Explore 页面 `gitee.com/explore` 可无授权访问。OAuth 作为 P2 增强 | 与现有爬虫架构一致，零额外复杂度 |
| **Q6** | AppGallery 审核周期 | 0.2.8 启动时同步提交审核草稿（不等待 QA 完成）。预计 5-7 个工作日 | 提前提交可并行等待；草稿可在审核期间更新 |
| **Q7** | 密码强度 | 最小 8 位 + 至少包含字母和数字（后端 + 前端双重校验）。不强制特殊字符 | 平衡安全性与用户体验；bcrypt 本身提供足够哈希强度 |

#### 4 项新 ADR（架构决策记录）

| ADR # | 决策 | 背景 | 影响 |
|-------|------|------|------|
| **ADR-001** | Refresh Token 存储在 localStorage（非 httpOnly cookie） | 三端统一：Tauri 不支持 httpOnly cookie（无浏览器环境）；Capacitor WebView 支持但跨域复杂 | 前端负责 refresh token 安全存储；access token 短时效（24h）降低泄露风险 |
| **ADR-002** | PostgreSQL 作为唯一生产数据库，SQLite 仅保留用于本地开发和测试 | 云部署需要 PostgreSQL（Supabase）；本地开发继续用 SQLite（零配置）；Alembic 迁移脚本确保两者 schema 一致 | `config.py` 中 `DATABASE_URL` 按环境切换；本地 `sqlite+aiosqlite:///./devpulse.db`，生产 `postgresql+asyncpg://...` |
| **ADR-003** | 鸿蒙不引入独立前端代码，所有 UI 来自 React SPA 构建产物 | 鸿蒙端通过 ArkUI Web 组件加载 `desktop/dist/`，仅容器层（标题栏、通知、存储）使用 ArkTS 原生实现 | 前端代码零分叉；鸿蒙特有逻辑通过 JsBridge 注入 `window.__HARMONY__` 全局对象 |
| **ADR-004** | LLM 摘要管线优先使用 DeepSeek，失败自动 fallback Qwen → Claude → GPT-4o-mini | DeepSeek ¥0.002/1K tokens（约 ¥0.02/次摘要），成本仅为 GPT-4o-mini 的 1/10 | 保留现有 4 厂商适配器，按价格排序的 fallback 链路；单次摘要失败不阻塞整体流程 |

---

## Part B: 任务分解

---

### 6. 依赖包列表

#### Python（backend/requirements.txt 新增）

```
alembic>=1.13.0,<2.0.0          # 数据库迁移管理
asyncpg>=0.29.0,<1.0.0          # PostgreSQL 异步驱动
psycopg2-binary>=2.9.9,<3.0.0   # PostgreSQL 同步驱动（Alembic 用）
pyjwt>=2.8.0,<3.0.0             # JWT 签发与验证
passlib[bcrypt]>=1.7.4,<2.0.0   # bcrypt 密码哈希
firebase-admin>=6.5.0,<7.0.0    # FCM 推送
```

#### npm（desktop/ + mobile/ package.json 新增）

```
# 移动端
@capacitor/push-notifications@^6.0.0   # FCM 推送 Capacitor 插件

# 桌面端（无新增生产依赖）
# AuthPage 使用现有 React Hook Form 或纯受控组件
```

#### Cargo（desktop/src-tauri/Cargo.toml）

```
# 无新增依赖（Tauri 2.x 现有插件体系已覆盖）
```

---

### 7. 任务列表

> **硬性约束**：总共 5 个任务，每个任务至少 3 个相关文件，按功能模块/层次分组。

| Task ID | 任务名称 | 覆盖版本 | 源文件数 | 依赖 |
|:-------:|---------|:-------:|:------:|:----:|
| **T01** | 项目基础设施 + Android 真机 + 后端云部署 | 0.2.1 + 0.2.2 | 15 | — |
| **T02** | 用户认证系统 + 跨端同步 | 0.2.3 | 11 | T01 |
| **T03** | 多源扩展 + 移动推送 | 0.2.4 + 0.2.5 | 15 | T02 |
| **T04** | 鸿蒙全链路（入门 + UI 适配） | 0.2.6 + 0.2.7 | 15 | T01 |
| **T05** | QA + 商店准备 + 鸿蒙发布 | 0.2.8 + 0.3.0 | 12 | T02, T03, T04 |

---

#### T01: 项目基础设施 + Android 真机 + 后端云部署

| 维度 | 内容 |
|------|------|
| **Task ID** | T01 |
| **任务名称** | 项目基础设施 + Android 真机 + 后端云部署 |
| **优先级** | P0 |
| **依赖** | 无 |

**源文件**：

| 文件 | 操作 |
|------|:----:|
| `backend/Dockerfile` | 🆕 多阶段构建（Python 3.11-slim + uvicorn） |
| `backend/docker-compose.yml` | 🆕 app + postgres 双服务，restart: unless-stopped |
| `backend/.dockerignore` | 🆕 Docker 构建排除 |
| `backend/alembic.ini` | 🆕 Alembic 配置 |
| `backend/migrations/env.py` | 🆕 异步 SQLAlchemy 迁移环境 |
| `backend/migrations/versions/001_initial_schema.py` | 🆕 初始 schema 迁移（含 users 表预留） |
| `backend/scripts/export_sqlite_to_pg.py` | 🆕 SQLite → PG 导出脚本 |
| `backend/devpulse/config.py` | ✏️ DATABASE_URL 环境切换、新增 `RENDER`/`API_BASE_URL` |
| `backend/devpulse/core/database.py` | ✏️ 支持 PostgreSQL asyncpg 连接（URL 前缀自动识别） |
| `backend/devpulse/main.py` | ✏️ `/health` 增强（DB 状态 + 最近周报时间）；lifespan 运行 Alembic |
| `mobile/android/app/build.gradle` | ✏️ Gradle 构建参数调优（增量 <2min） |
| `mobile/capacitor.config.ts` | ✏️ webDir 路径修正、server.url 配置 |
| `desktop/src/index.css` | ✏️ 移动端 48px 最小触摸区域、滚动优化 |
| `desktop/src/components/TrendingList.tsx` | ✏️ 下拉刷新 + 上拉加载更多 |
| `desktop/src/utils/api-client.ts` | ✏️ `detectBaseUrl()` 添加 `VITE_API_BASE` 环境变量优先级 |

**验收标准**：
1. `docker-compose up` → `curl localhost:8000/health` 返回 `{"db_status": "connected"}`
2. SQLite 历史数据通过导出脚本成功导入 PostgreSQL，查询验证一致
3. Android USB 真机 `npx cap open android` → 首页 Trending 列表正常渲染
4. 所有可点击元素宽高 ≥ 48px（移动端）
5. Gradle 增量构建 < 2 分钟，clean 构建 < 5 分钟

---

#### T02: 用户认证系统 + 跨端同步

| 维度 | 内容 |
|------|------|
| **Task ID** | T02 |
| **任务名称** | 用户认证系统 + 跨端同步 |
| **优先级** | P0 |
| **依赖** | T01（PostgreSQL 就绪） |

**源文件**：

| 文件 | 操作 |
|------|:----:|
| `backend/devpulse/core/models.py` | ✏️ 新增 `User` 模型；`Favorite.user_id` 关联 `users.id`（外键） |
| `backend/devpulse/api/endpoints/auth.py` | 🆕 `/auth/register`、`/auth/login`、`/auth/me`、`/auth/refresh` |
| `backend/devpulse/api/dependencies.py` | 🆕 `get_current_user` Bearer Token 依赖注入 |
| `backend/devpulse/services/auth_service.py` | 🆕 bcrypt 哈希、JWT 签发/验证、refresh token 轮换 |
| `backend/devpulse/api/endpoints/repos.py` | ✏️ 收藏/取消收藏端点从 JWT 解析 user_id |
| `desktop/src/pages/AuthPage.tsx` | 🆕 登录/注册双 Tab；邮箱验证、密码强度、错误状态 |
| `desktop/src/components/ProtectedRoute.tsx` | 🆕 路由守卫：未登录 → `/auth` |
| `desktop/src/stores/useAuthStore.ts` | 🆕 Zustand：user/token/refresh/logout/401 拦截 |
| `desktop/src/utils/api-client.ts` | ✏️ `Authorization: Bearer` 自动注入；401 → refresh → 重试 |
| `desktop/src/types/index.ts` | ✏️ 新增 `User`、`AuthResponse`、`LoginRequest`、`RegisterRequest` |
| `desktop/src/App.tsx` | ✏️ 新增 `/auth` 路由；AuthPage 独立布局 |

**验收标准**：
1. 注册 → 邮箱格式/密码强度前端校验通过 → POST /auth/register → 返回 JWT
2. 登录 → POST /auth/login → Token 持久化 localStorage → 自动跳转首页
3. 设备 A 收藏 → 设备 B 登录同账号 → 收藏列表一致
4. Token 过期（24h）→ 401 → 自动 refresh → 无感续期
5. refresh token 也过期（7d）→ 跳转登录页

---

#### T03: 多源扩展 + 移动推送

| 维度 | 内容 |
|------|------|
| **Task ID** | T03 |
| **任务名称** | 多源扩展 + 移动推送 |
| **优先级** | P1 |
| **依赖** | T02（用户系统用于 FCM token 关联 + 推送偏好） |

**源文件**：

| 文件 | 操作 |
|------|:----:|
| `backend/devpulse/services/trending_source.py` | 🆕 `TrendingSource` 抽象基类 + `GitHubSource`/`GitLabSource`/`GiteeSource` |
| `backend/devpulse/services/trending_scraper.py` | ✏️ 重构：`source` 参数 → 工厂方法创建对应 Source |
| `backend/devpulse/api/endpoints/repos.py` | ✏️ `/trending?source=gitlab`、`/languages` 端点 |
| `backend/devpulse/services/fcm_service.py` | 🆕 Firebase Admin SDK：register_token、multicast、send_to_user |
| `backend/devpulse/api/endpoints/auth.py` | ✏️ `PUT /user/fcm-token`、`PUT /user/preferences` |
| `backend/devpulse/services/scheduler.py` | ✏️ 周报生成后 → `fcm_service.send_weekly_report_notification()` |
| `backend/devpulse/config.py` | ✏️ `FCM_CREDENTIALS_PATH`、`SUPPORTED_LANGUAGES` |
| `desktop/src/components/DataSourceTabs.tsx` | 🆕 GitHub/GitLab/Gitee 三 Tab 切换 |
| `desktop/src/components/LanguageFilter.tsx` | 🆕 20+ 语言多选下拉（搜索 + 分组） |
| `desktop/src/pages/TrendingPage.tsx` | ✏️ 集成 DataSourceTabs + LanguageFilter |
| `desktop/src/pages/SettingsPage.tsx` | ✏️ 推送开关（周报推送/重要项目推送）+ 云同步标识 |
| `desktop/src/stores/useTrendingStore.ts` | ✏️ `source`/`language` 参数 + API 调用适配 |
| `desktop/src/stores/useNotificationStore.ts` | ✏️ `fcmToken` 管理 + 偏好同步 `PUT /user/preferences` |
| `mobile/package.json` | ✏️ `@capacitor/push-notifications@^6.0.0` |
| `mobile/capacitor.config.ts` | ✏️ PushNotifications 插件声明 |

**验收标准**：
1. Trending 页切换 GitHub/GitLab/Gitee Tab → API 请求不同 source → 列表更新
2. 语言筛选器 ≥ 20 个选项，支持搜索和多选
3. `GitHubSource`/`GitLabSource`/`GiteeSource` 各自通过单元测试
4. 新增数据源只需继承 `TrendingSource` 并实现 2 个方法
5. 后端周报生成 → FCM 广播 → Android 通知栏弹出（国外网络环境）
6. Web 端修改推送偏好 → Android 端生效（偏好云同步）

---

#### T04: 鸿蒙全链路（入门 + UI 适配）

| 维度 | 内容 |
|------|------|
| **Task ID** | T04 |
| **任务名称** | 鸿蒙全链路（入门 + UI 适配） |
| **优先级** | P1 |
| **依赖** | T01（`API_BASE_URL` 环境变量就绪，用于鸿蒙远端连接） |

**源文件**：

| 文件 | 操作 |
|------|:----:|
| `harmony/build-profile.json5` | 🆕 DevEco Studio 构建配置（SDK API 12+） |
| `harmony/entry/src/main/module.json5` | 🆕 模块声明：INTERNET/NOTIFICATION 权限、Web 组件配置 |
| `harmony/entry/src/main/ets/pages/Index.ets` | 🆕 ArkUI 入口页：Web 组件加载远端 `API_BASE_URL` 或本地 `dist/` |
| `harmony/entry/src/main/ets/webview/WebViewContainer.ets` | 🆕 WebView 容器：加载状态、错误重试、JS Bridge 初始化 |
| `harmony/entry/src/main/ets/bridge/JsBridge.ets` | 🆕 JS ↔ ArkTS 双向通信：通知、存储、设备信息、路由跳转 |
| `harmony/entry/src/main/ets/notification/NotificationService.ets` | 🆕 @ohos.notificationManager：周报推送、通知点击跳转 |
| `harmony/entry/src/main/ets/pages/TitleBar.ets` | 🆕 ArkUI 原生标题栏（替代 Web 内导航）：返回按钮 + 标题 + 菜单 |
| `harmony/entry/src/main/ets/pages/SafeAreaWrapper.ets` | 🆕 刘海屏 safe-area 适配：`window.getLastWindow().getWindowAvoidArea()` |
| `harmony/entry/src/main/ets/storage/PreferencesStore.ets` | 🆕 @ohos.data.preferences 本地缓存：离线周报数据 |
| `harmony/entry/src/main/ets/entryability/EntryAbility.ets` | 🆕 应用生命周期：通知权限请求、手势返回拦截 |
| `harmony/entry/src/main/resources/base/element/string.json` | 🆕 字符串资源（中文） |
| `harmony/hvigor/hvigor-config.json5` | 🆕 Hvigor 构建配置 |
| `scripts/build_harmony_webview.sh` | 🆕 构建前端 → 复制 dist/ 到 harmony/webview/rawfile/ |
| `desktop/src/index.css` | ✏️ `env(safe-area-inset-*)` 鸿蒙 safe-area CSS 变量 |
| `desktop/src/components/Layout.tsx` | ✏️ 鸿蒙模式检测：隐藏 Web 导航栏（由原生 TitleBar 接管） |

**验收标准**：
1. DevEco Studio 模拟器 → WebView 加载 → Trending 列表正常渲染
2. 鸿蒙通知栏弹出新周报通知 → 点击通知 → 跳转对应周报详情
3. 刘海屏区域内容不被遮挡（safe-area inset 正确）
4. 侧滑返回手势正常触发（页面栈管理正确）
5. 离线环境下打开 App → 展示上次缓存的周报数据
6. 前端 SPA 路由（/、/search、/repo/:owner/:repo）在鸿蒙 WebView 中均可访问

---

#### T05: QA + 商店准备 + 鸿蒙发布

| 维度 | 内容 |
|------|------|
| **Task ID** | T05 |
| **任务名称** | QA + 商店准备 + 鸿蒙发布 |
| **优先级** | P0（阻塞发布） |
| **依赖** | T02（用户系统回归）、T03（推送回归）、T04（鸿蒙回归） |

**源文件**：

| 文件 | 操作 |
|------|:----:|
| `docs/test_matrix_phase3.md` | 🆕 三端 30+ 测试用例（Win/Android/鸿蒙） |
| `docs/privacy_policy.md` | 🆕 隐私政策（中文，符合 AppGallery 要求） |
| `docs/appgallery_listing.md` | 🆕 商店上架文案（标题/短描述/完整描述/关键词） |
| `docs/release_notes_0.3.0.md` | 🆕 0.3.0 版本发布说明 |
| `docs/screenshots/win_trending.png` | 🆕 Windows 桌面端截图 |
| `docs/screenshots/android_trending.png` | 🆕 Android 移动端截图 |
| `docs/screenshots/harmony_trending.png` | 🆕 鸿蒙移动端截图 |
| `desktop/src/pages/PrivacyPage.tsx` | 🆕 App 内隐私政策展示页（Markdown 渲染） |
| `desktop/src/components/AccessibilityWrapper.tsx` | 🆕 aria-label、role、tabIndex 无障碍增强 |
| `desktop/src/App.tsx` | ✏️ 新增 `/privacy` 路由 |
| `harmony/entry/src/main/resources/base/profile/agconnect-services.json` | 🆕 AppGallery Connect 配置 |
| `harmony/build-profile.json5` | ✏️ 签名配置（debug/release 证书 SHA256） |
| `scripts/sign_hap.sh` | 🆕 HAP 签名打包（CI 自动化：hvigor assembleHap + hap-sign-tool） |
| `scripts/upload_appgallery.sh` | 🆕 AppGallery Connect API 上传（agc-manager CLI） |

**验收标准**：
1. 三端回归测试通过率 > 95%（Win 12 用例 + Android 10 用例 + 鸿蒙 10 用例）
2. AppGallery 审核材料齐全：3 张截图（≥1280×800）、隐私政策 URL、应用描述（中文）
3. HAP 签名打包自动化：CI 产出 signed .hap 文件
4. AppGallery Connect 上传成功 → 审核状态可查询
5. 无障碍：TalkBack/鸿蒙屏幕朗读可正确朗读页面核心内容
6. 性能：首屏 FCP < 2s（Lighthouse 移动端模拟）

---

### 8. 共享知识

#### 8.1 通用约定

```
- 所有 API 响应格式：{"code": 0, "message": "success", "data": {...}}
- JWT access_token 有效期 24 小时，refresh_token 有效期 7 天
- 密码哈希使用 bcrypt（passlib），cost factor = 12
- 所有日期时间字段使用 ISO 8601 UTC 格式
- 爬虫 User-Agent 统一为 "DevPulse/0.3.0"
- 前端 API 调用统一经过 api-client.ts，禁止直接 fetch
- Git 提交格式：feat: / fix: / docs: / refactor: / test: / chore:
```

#### 8.2 数据库迁移规范

```
1. 所有 schema 变更通过 Alembic 迁移脚本执行
2. 迁移文件命名：versions/{序号}_{描述}.py（如 001_initial_schema.py）
3. 使用 async SQLAlchemy（asyncpg 驱动），迁移脚本需同时兼容 sync engine（Alembic 要求）
4. 迁移前自动备份：export_sqlite_to_pg.py 先 dump SQLite → JSON 文件
5. 迁移后校验：记录数对比（SELECT count(*) FROM each_table）
6. 回滚方案：保留 SQLite 文件 + 迁移前 JSON 备份
```

#### 8.3 环境变量清单

```bash
# ── 必填（生产环境）──────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/devpulse  # PostgreSQL 连接串
JWT_SECRET_KEY=<random-256-bit-hex>                              # JWT HS256 签名密钥
FCM_CREDENTIALS_PATH=/app/firebase-credentials.json              # Firebase Admin SDK 密钥文件

# ── 可选（生产环境）──────────────────────────
DEEPSEEK_API_KEY=sk-xxx          # LLM 摘要（推荐）
LLM_PROVIDER=deepseek            # deepseek | openai | anthropic | ollama
CORS_ORIGINS=["https://devpulse.app","capacitor://localhost"]

# ── 前端构建时注入 ───────────────────────────
VITE_API_BASE=https://api.devpulse.app   # 移动端/鸿蒙远端 API 地址
```

#### 8.4 Docker Compose 服务定义

```yaml
# backend/docker-compose.yml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://devpulse:${DB_PASSWORD}@db:5432/devpulse
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: devpulse
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: devpulse
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devpulse"]
      interval: 10s
      retries: 5

volumes:
  pgdata:
```

#### 8.5 鸿蒙开发约定

```
- 语言：ArkTS（TypeScript 超集）
- API Level：API 12+（HarmonyOS NEXT 5.0）
- Web 组件必须声明 .domStorageAccess(true) 以支持 localStorage
- JS Bridge 通过 window.__HARMONY__ 全局对象暴露原生能力
- 前端检测鸿蒙环境：navigator.userAgent.includes("HarmonyOS") 或 window.__HARMONY__ !== undefined
- 鸿蒙端禁止独立 UI 代码，所有页面内容由 React SPA 渲染
```

---

### 9. 任务依赖图

```mermaid
graph TD
    T01["T01: 基础设施 + Android真机 + 云部署<br/>0.2.1 + 0.2.2<br/>P0 | 15 files | 无依赖"]
    T02["T02: 用户认证系统 + 跨端同步<br/>0.2.3<br/>P0 | 11 files | 依赖 T01"]
    T03["T03: 多源扩展 + 移动推送<br/>0.2.4 + 0.2.5<br/>P1 | 15 files | 依赖 T02"]
    T04["T04: 鸿蒙全链路<br/>0.2.6 + 0.2.7<br/>P1 | 15 files | 依赖 T01"]
    T05["T05: QA + 商店准备 + 鸿蒙发布<br/>0.2.8 + 0.3.0<br/>P0 | 12 files | 依赖 T02,T03,T04"]

    T01 --> T02
    T01 --> T04
    T02 --> T03
    T02 --> T05
    T03 --> T05
    T04 --> T05

    style T01 fill:#4CAF50,color:#fff
    style T02 fill:#2196F3,color:#fff
    style T03 fill:#FF9800,color:#fff
    style T04 fill:#9C27B0,color:#fff
    style T05 fill:#F44336,color:#fff
```

> **关键路径**：T01 → T02 → T05（约占总工期的关键链）  
> **并行策略**：T02（用户系统）和 T04（鸿蒙）可并行推进，T03（多源+推送）在 T02 完成后可与 T04 并行。
