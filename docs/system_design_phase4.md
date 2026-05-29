# DevPulse Phase 4 系统架构设计（0.3.1 → 0.4.0）

> **架构师**: Bob（高见远）
> **基线版本**: 0.3.0（三端发布完成）
> **目标版本**: 0.4.0（v1.0.0-rc，生产级发布）
> **设计日期**: 2026-05-29

---

## Part A: 系统设计

---

### 1. 实现方案

#### 1.1 核心技术挑战

| 挑战 | 描述 | 严重度 |
|------|------|--------|
| **生产部署迁移** | 从本地 SQLite+Tauri 嵌入式架构迁移到 VPS Docker + PostgreSQL + Nginx 公网部署 | 🔴 高 |
| **推荐引擎冷启动** | 用户量 <1000 时协同过滤稀疏矩阵几乎不可用，需要多层降级策略 | 🟡 中 |
| **PWA 离线策略** | API 数据、静态资源、图片的差异化缓存策略需精确控制，避免过期数据 | 🟡 中 |
| **i18n 全覆盖** | 三语种需要覆盖 UI 文案、LLM 生成内容标签、SEO meta 标签 | 🟢 低 |
| **管理后台安全** | Admin API 需要角色鉴权，避免越权操作（封禁/解禁/爬虫触发） | 🔴 高 |

#### 1.2 架构模式

```
┌──────────────────────────────────────────────────────────────┐
│                   Internet (HTTPS)                            │
│                        │                                      │
│              ┌─────────▼──────────┐                           │
│              │  Cloudflare CDN    │ (免费计划: DDoS/缓存/SSL)  │
│              └─────────┬──────────┘                           │
│                        │                                      │
│              ┌─────────▼──────────┐                           │
│              │  Nginx (VPS)       │ 反向代理 + SSL Termination │
│              │  - /api/* → :8000  │ brotli/gzip + 静态文件     │
│              │  - /     → :1420   │                           │
│              └────┬──────────┬────┘                           │
│                   │          │                                │
│     ┌─────────────▼──┐  ┌───▼──────────────┐                 │
│     │ FastAPI :8000   │  │ React SPA :1420  │                 │
│     │ (Docker)        │  │ (Nginx static)   │                 │
│     │ - PostgreSQL    │  │ - PWA SW         │                 │
│     │ - Sentry SDK    │  │ - react-i18next  │                 │
│     │ - scikit-learn  │  │ - @sentry/react  │                 │
│     └────────┬────────┘  └──────────────────┘                 │
│              │                                                │
│     ┌────────▼────────┐                                      │
│     │ PostgreSQL 16    │                                      │
│     │ (Docker Volume)  │                                      │
│     └─────────────────┘                                      │
└──────────────────────────────────────────────────────────────┘
```

#### 1.3 框架与库选型

| 领域 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 反向代理 | Nginx | 1.25+ | 成熟稳定，brotli 模块内置 |
| SSL | Let's Encrypt + certbot | latest | 免费自动化续期 |
| 错误追踪 | Sentry | SDK 2.x (Python) / 8.x (React) | 免费 tier 5K errors/month |
| CDN | Cloudflare | Free Plan | 全球节点、DDoS、自动 HTTPS |
| 推荐引擎 | scikit-learn | 1.5.x | cosine_similarity 轻量无 GPU |
| PWA | vite-plugin-pwa + Workbox | 0.20.x | Vite 原生集成，自动 SW 生成 |
| i18n | react-i18next | 14.x | React 生态最成熟方案 |
| 分享图生成 | Pillow | 10.x | Python 图片合成（Canvas 在 Node 端不可用） |
| 压力测试 | wrk | 4.x | 轻量 HTTP 基准工具 |
| 分析 | GA4 (gtag) | latest | 免费，全平台 |

#### 1.4 关键设计决策

**推荐引擎冷启动策略（三层降级）**：

```
用户请求推荐
    │
    ├── L1: 协同过滤 (用户 ≥ 3 条行为记录)
    │       → scikit-learn cosine_similarity on user-repo matrix
    │
    ├── L2: 内容过滤 (用户 < 3 条记录但有关注语言)
    │       → 基于 topics/language 匹配的热门项目
    │
    └── L3: 全局热门 (新用户，零行为)
            → trending_rank ASC, 按 total_stars 降序
```

**PWA Service Worker 缓存策略**：

| 资源类型 | 策略 | 缓存时长 | 最大条目 |
|---------|------|---------|---------|
| 静态资源 (JS/CSS/字体) | CacheFirst | 30 天 | 100 |
| 图片 (PNG/WebP/SVG) | CacheFirst | 7 天 | 200 |
| API 响应 (trending/weekly) | NetworkFirst | 5 分钟 | 50 |
| API 响应 (repo detail) | NetworkFirst | 1 小时 | 100 |
| HTML (SPA shell) | NetworkFirst | - | 1 |

**i18n 文件结构**：

```
desktop/src/locales/
├── zh/
│   ├── common.json      # 通用文案（导航/按钮/状态）
│   ├── trending.json    # Trending 页面
│   ├── detail.json      # 详情页
│   ├── auth.json        # 认证页面
│   ├── settings.json    # 设置页面
│   ├── admin.json       # 管理后台
│   └── recommendation.json  # 推荐理由模板
├── en/  (同上结构)
└── ja/  (同上结构)
```

**i18n key 命名规范**：`命名空间.模块.组件.属性` 如 `common.nav.trending.label`

---

### 2. 文件列表

#### 2.1 0.3.1 生产部署

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/nginx/nginx.conf` | **NEW** | Nginx 主配置：反向代理 + SSL + brotli |
| `backend/nginx/conf.d/default.conf` | **NEW** | 站点配置：API 代理 + 静态文件 |
| `backend/nginx/conf.d/ssl.conf` | **NEW** | SSL 配置模板（Let's Encrypt） |
| `docker-compose.prod.yml` | **NEW** | 生产环境 Docker Compose（Nginx + API + DB） |
| `.env.production.example` | **NEW** | 生产环境变量模板 |
| `backend/devpulse/config.py` | **MODIFY** | 新增 SENTRY_DSN、ENVIRONMENT、DEPLOY_MODE |
| `backend/requirements-docker.txt` | **MODIFY** | 新增 sentry-sdk、pillow |
| `backend/Dockerfile` | **MODIFY** | 构建阶段优化，添加 sentry 初始化 |
| `desktop/src/main.tsx` | **MODIFY** | 初始化 Sentry（`@sentry/react`） |
| `desktop/vite.config.ts` | **MODIFY** | 新增 `VITE_SENTRY_DSN` / `VITE_API_BASE` 环境变量注入 |
| `desktop/package.json` | **MODIFY** | 新增 `@sentry/react`、`@sentry/vite-plugin` |

#### 2.2 0.3.2 内容品控

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/devpulse/core/models.py` | **MODIFY** | Repository 新增 `confidence_score`、`review_status` 字段 |
| `backend/devpulse/api/endpoints/admin.py` | **NEW** | 审核端点：`/admin/pending-reviews`、`/admin/approve` |
| `backend/devpulse/services/content_quality.py` | **NEW** | 置信度评分服务：关键词覆盖度 + 摘要长度 + 句式完整性 |
| `backend/devpulse/services/scheduler.py` | **MODIFY** | 新增周一 09:00 自动生成 + 10:00 自动发布任务 |
| `backend/devpulse/services/storage.py` | **MODIFY** | crawl 后自动计算 confidence_score |

#### 2.3 0.3.3 用户互动

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/devpulse/core/models.py` | **MODIFY** | 新增 `Comment`、`Like` 模型 |
| `backend/devpulse/api/endpoints/interactions.py` | **NEW** | 评论/点赞/分享端点 |
| `backend/devpulse/services/interaction_service.py` | **NEW** | 互动统计聚合服务 |
| `backend/devpulse/services/share_image.py` | **NEW** | Pillow 分享图生成服务 |
| `desktop/src/pages/RepoDetailPage.tsx` | **MODIFY** | 新增评论列表 + 评论输入框 + 点赞按钮 + 分享按钮 |
| `desktop/src/components/CommentSection.tsx` | **NEW** | 评论区组件（列表 + 输入 + 回复） |
| `desktop/src/components/ShareMenu.tsx` | **NEW** | 分享菜单（复制链接 + 下载图片） |
| `desktop/src/stores/useInteractionStore.ts` | **NEW** | 互动状态管理（评论/点赞计数） |
| `desktop/src/types/index.ts` | **MODIFY** | 新增 Comment、Like、ShareImage 类型 |

#### 2.4 0.3.4 AI 推荐

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/devpulse/core/models.py` | **MODIFY** | 新增 `UserBehavior` 模型 |
| `backend/devpulse/services/recommendation.py` | **NEW** | 推荐引擎：协同过滤 + 内容过滤 + 热门降级 |
| `backend/devpulse/api/endpoints/recommendations.py` | **NEW** | `GET /repos/recommended` 推荐端点 |
| `backend/requirements-docker.txt` | **MODIFY** | 新增 scikit-learn |
| `desktop/src/pages/TrendingPage.tsx` | **MODIFY** | 新增"为你推荐"Tab |
| `desktop/src/components/RecommendationList.tsx` | **NEW** | 推荐列表组件（含推荐理由） |
| `desktop/src/stores/useRecommendationStore.ts` | **NEW** | 推荐状态管理 |
| `desktop/src/types/index.ts` | **MODIFY** | 新增 RecommendationItem 类型 |

#### 2.5 0.3.5 性能优化 + PWA + CDN

| 路径 | 操作 | 说明 |
|------|------|------|
| `desktop/vite.config.ts` | **MODIFY** | `manualChunks` + `vite-plugin-pwa` 配置 |
| `desktop/src/App.tsx` | **MODIFY** | `React.lazy()` + `Suspense` 路由级分割 |
| `desktop/public/manifest.json` | **NEW** | PWA manifest（图标/名称/主题色） |
| `desktop/public/sw.js` | **NEW** | Service Worker 入口（Workbox 生成） |
| `desktop/public/offline.html` | **NEW** | 离线回退页面 |
| `desktop/package.json` | **MODIFY** | 新增 `vite-plugin-pwa`、`workbox-precaching` |
| `desktop/src/components/ImageWithLazy.tsx` | **NEW** | 图片懒加载包装组件 |
| `backend/nginx/conf.d/gzip.conf` | **NEW** | gzip/brotli 压缩配置 |

#### 2.6 0.3.6 管理后台

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/devpulse/core/models.py` | **MODIFY** | User 新增 `role` 字段（user/admin）；新增 `DailyStats` 模型 |
| `backend/devpulse/api/endpoints/admin.py` | **MODIFY** | 新增 Dashboard 统计、用户管理、爬虫触发端点 |
| `backend/devpulse/api/dependencies.py` | **MODIFY** | 新增 `require_admin` 依赖注入 |
| `backend/devpulse/services/admin_service.py` | **NEW** | 管理后台业务服务（统计聚合） |
| `desktop/src/pages/AdminPage.tsx` | **NEW** | 管理后台页面（仅 admin 可见） |
| `desktop/src/components/admin/DashboardCards.tsx` | **NEW** | 数据看板卡片组（DAU/阅读量/收藏/LLM成本） |
| `desktop/src/components/admin/UserManagement.tsx` | **NEW** | 用户管理列表 + 封禁/解禁 |
| `desktop/src/components/admin/AdminCharts.tsx` | **NEW** | Recharts 管理图表（趋势折线图） |
| `desktop/src/components/Layout.tsx` | **MODIFY** | 导航栏新增 Admin 入口（role=admin 可见） |
| `desktop/src/stores/useAdminStore.ts` | **NEW** | 管理后台状态管理 |

#### 2.7 0.3.7 多语言 + SEO

| 路径 | 操作 | 说明 |
|------|------|------|
| `desktop/src/i18n.ts` | **NEW** | i18next 初始化配置（语言检测 + 资源加载） |
| `desktop/src/locales/zh/*.json` | **NEW** | 中文翻译文件（7 个命名空间） |
| `desktop/src/locales/en/*.json` | **NEW** | 英文翻译文件 |
| `desktop/src/locales/ja/*.json` | **NEW** | 日文翻译文件 |
| `desktop/src/components/LanguageSwitcher.tsx` | **NEW** | 语言切换组件（下拉选择器） |
| `desktop/src/components/Layout.tsx` | **MODIFY** | 集成 LanguageSwitcher |
| `desktop/src/components/SEOHead.tsx` | **NEW** | 动态 `<meta>` SEO 标签组件 |
| `desktop/index.html` | **MODIFY** | 多语言 `<html lang>` + GA4 脚本 |
| `desktop/package.json` | **MODIFY** | 新增 `react-i18next`、`i18next`、`i18next-browser-languagedetector` |
| `backend/devpulse/api/endpoints/seo.py` | **NEW** | sitemap.xml 动态生成端点 |
| `backend/devpulse/main.py` | **MODIFY** | 注册 seo 路由 |

#### 2.8 0.3.8 QA + 0.4.0 发布

| 路径 | 操作 | 说明 |
|------|------|------|
| `backend/devpulse/__init__.py` | **MODIFY** | `__version__ = "0.4.0"` |
| `desktop/package.json` | **MODIFY** | `"version": "0.4.0"` |
| `CHANGELOG.md` | **NEW** | 0.3.1 → 0.4.0 完整变更日志 |
| `docs/test-matrix-phase4.md` | **NEW** | Phase 4 三端全量测试矩阵 |
| `scripts/benchmark.sh` | **NEW** | wrk 压测脚本 |
| `backend/devpulse/core/models.py` | **MODIFY** | `__version__` 同步 |

---

### 3. 数据结构与接口

#### 3.1 核心数据模型

```mermaid
classDiagram
    direction TB

    class User {
        +int id PK
        +str email UK
        +str password_hash
        +str display_name
        +str role "user|admin"
        +bool is_active
        +bool push_enabled
        +bool push_weekly_report
        +bool push_important_project
        +str fcm_token
        +datetime created_at
        +datetime updated_at
    }

    class Repository {
        +int id PK
        +str full_name UK
        +str owner
        +str name
        +str description
        +str language
        +list~str~ topics
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
        +list~str~ key_points
        +list~str~ tags
        +float confidence_score
        +str review_status "pending|approved|rejected"
        +datetime crawled_at
        +datetime summarized_at
        +int trending_rank
        +str trending_since
        +str source
    }

    class Comment {
        +int id PK
        +int user_id FK
        +int repo_id FK
        +str content
        +int parent_id FK
        +bool is_deleted
        +datetime created_at
        +datetime updated_at
    }

    class Like {
        +int id PK
        +int user_id FK
        +int repo_id FK
        +datetime created_at
    }

    class UserBehavior {
        +int id PK
        +int user_id FK
        +int repo_id FK
        +str action_type "view|star|like|share|comment"
        +float weight
        +datetime created_at
    }

    class Favorite {
        +int id PK
        +int user_id FK
        +int repo_id FK
        +datetime created_at
    }

    class DailyStats {
        +int id PK
        +date date UK
        +int dau
        +int page_views
        +int new_users
        +int crawl_count
        +float llm_cost
        +datetime created_at
    }

    class WeeklyReport {
        +int id PK
        +datetime week_start UK
        +datetime week_end
        +str language_filter
        +str source_filter
        +int total_repos
        +list~int~ top_repos
        +str overview_text
        +datetime generated_at
        +bool published
        +datetime published_at
    }

    User "1" -- "N" Comment
    User "1" -- "N" Like
    User "1" -- "N" UserBehavior
    User "1" -- "N" Favorite
    Repository "1" -- "N" Comment
    Repository "1" -- "N" Like
    Repository "1" -- "N" UserBehavior
    Repository "1" -- "N" Favorite
    Comment "1" -- "N" Comment : parent
    User "1" -- "N" DailyStats : tracked by
```

#### 3.2 API 请求/响应格式

**通用响应格式**（保持现有）：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "pagination": { "page": 1, "page_size": 25, "total": 156 }
}
```

**新增端点一览**：

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/repos/recommended` | optional | 个性化推荐列表 |
| `POST` | `/repos/{full_name}/comments` | required | 发表评论 |
| `GET` | `/repos/{full_name}/comments` | optional | 评论列表（分页） |
| `DELETE` | `/repos/{full_name}/comments/{id}` | required | 删除评论（本人/admin） |
| `POST` | `/repos/{full_name}/like` | required | 点赞（toggle） |
| `GET` | `/repos/{full_name}/interactions` | optional | 互动统计 |
| `GET` | `/repos/{full_name}/share-image` | optional | 生成分享图 |
| `GET` | `/admin/dashboard` | admin | Dashboard 统计数据 |
| `GET` | `/admin/users` | admin | 用户列表（分页） |
| `PUT` | `/admin/users/{id}/ban` | admin | 封禁/解禁用户 |
| `PUT` | `/admin/users/{id}/role` | admin | 修改用户角色 |
| `GET` | `/admin/pending-reviews` | admin | 待审核项目列表 |
| `POST` | `/admin/reviews/{id}/approve` | admin | 审核通过 |
| `POST` | `/admin/reviews/{id}/reject` | admin | 审核拒绝 |
| `POST` | `/admin/trigger-crawl` | admin | 手动触发爬虫 |
| `GET` | `/seo/sitemap.xml` | none | 动态 sitemap |

**置信度评分数据结构**：

```json
{
  "confidence_score": 0.85,
  "score_breakdown": {
    "keyword_coverage": 0.9,
    "summary_length": 0.8,
    "sentence_completeness": 0.85,
    "language_consistency": 0.85
  },
  "review_status": "pending",
  "low_confidence_flags": []
}
```

**推荐响应格式**：

```json
{
  "items": [
    {
      "repo": { "...Repo..." },
      "recommendation_reason": "与你收藏的 'transformers' 相似",
      "score": 0.92,
      "method": "collaborative"
    }
  ],
  "method": "collaborative",
  "fallback_level": 1
}
```

**分享图生成响应**：

```json
{
  "image_url": "/api/v1/repos/microsoft/graphrag/share-image",
  "width": 1200,
  "height": 630,
  "format": "png"
}
```

---

### 4. 程序调用流

#### 4.1 评论/点赞/分享交互流

```mermaid
sequenceDiagram
    actor User
    participant React as React SPA
    participant API as FastAPI :8000
    participant DB as PostgreSQL
    participant Pillow as Pillow Service

    Note over User, Pillow: ── 评论流程 ──

    User->>React: 输入评论 + 点击发送
    React->>API: POST /repos/{full_name}/comments<br/>{content, parent_id?}
    API->>API: JWT 认证
    API->>DB: INSERT INTO comments
    API-->>React: {comment_id, created_at}
    React->>React: 乐观更新评论列表

    Note over User, Pillow: ── 点赞流程 (Toggle) ──

    User->>React: 点击 👍
    React->>API: POST /repos/{full_name}/like
    API->>DB: SELECT like WHERE user_id+repo_id
    alt 未点赞
        API->>DB: INSERT INTO likes
        API->>DB: INSERT INTO user_behaviors (action='like')
        API-->>React: {liked: true, count: 129}
    else 已点赞
        API->>DB: DELETE FROM likes
        API-->>React: {liked: false, count: 128}
    end

    Note over User, Pillow: ── 分享流程 ──

    User->>React: 点击分享
    React->>React: 弹出 ShareMenu
    alt 复制链接
        React->>React: navigator.clipboard.writeText(url)
    else 生成分享图
        React->>API: GET /repos/{full_name}/share-image
        API->>Pillow: 生成分享图 (1200x630)
        Pillow-->>API: PNG bytes
        API-->>React: image/png
        React->>React: 触发下载
    end
```

#### 4.2 推荐引擎训练/预测流

```mermaid
sequenceDiagram
    actor User
    participant React as React SPA
    participant API as FastAPI :8000
    participant RecSvc as RecommendationService
    participant DB as PostgreSQL
    participant SK as scikit-learn

    Note over User, SK: ── 后台：行为数据积累 ──

    API->>DB: 每次 view/star/like 写入 user_behaviors

    Note over User, SK: ── 前台：推荐请求 ──

    User->>React: 切换到"为你推荐"Tab
    React->>API: GET /repos/recommended?limit=25<br/>Authorization: Bearer <token>
    API->>API: JWT 认证 (get_optional_user)

    alt 已登录用户
        API->>RecSvc: get_recommendations(user_id, limit=25)
        RecSvc->>DB: SELECT user_behaviors WHERE user_id
        DB-->>RecSvc: [3条行为记录]

        alt 行为 ≥ 3 条 (L1 协同过滤)
            RecSvc->>DB: SELECT all user_behaviors (user-repo matrix)
            RecSvc->>SK: cosine_similarity(matrix)
            SK-->>RecSvc: 相似用户 + 高分项目
            RecSvc->>DB: SELECT repos WHERE id IN (...)
            RecSvc-->>API: [{repo, score, reason, method:"collaborative"}]

        else 行为 < 3 条但有语言偏好 (L2 内容过滤)
            RecSvc->>DB: SELECT repos WHERE language IN (...) ORDER BY total_stars DESC
            RecSvc-->>API: [{repo, score, reason, method:"content"}]

        else 零行为 (L3 全局热门)
            RecSvc->>DB: SELECT repos ORDER BY trending_rank ASC, total_stars DESC
            RecSvc-->>API: [{repo, score, reason, method:"popular"}]
        end

    else 匿名用户
        API->>RecSvc: 直接降级到 L3 全局热门
    end

    API-->>React: {items: [...], method: "collaborative", fallback_level: 1}
    React->>React: 渲染推荐卡片（含推荐理由）
```

#### 4.3 内容审核 → 定时发布流

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant Crawler as Crawler Service
    participant LLM as LLM Summarizer
    participant Quality as ContentQuality Service
    participant DB as PostgreSQL
    participant Admin as Admin (React)
    participant Publisher as Publisher

    Note over Scheduler, Publisher: ── 周一 09:00 自动生成 ──

    Scheduler->>Crawler: 触发爬取 (cron: mon 09:00)
    Crawler->>Crawler: Playwright 抓取 GitHub Trending
    Crawler->>LLM: 逐项目生成摘要
    LLM-->>Crawler: 摘要结果
    Crawler->>Quality: 计算置信度评分
    Quality->>Quality: keyword_coverage × summary_length × sentence_completeness
    Quality-->>Crawler: confidence_score + review_status

    alt confidence_score ≥ 0.7
        Crawler->>DB: review_status = "approved"
    else confidence_score < 0.7
        Crawler->>DB: review_status = "pending" (待人工审核)
    end

    Crawler->>DB: 写入 Repository (含 score + status)

    Note over Scheduler, Publisher: ── 管理员审核 ──

    Admin->>DB: GET /admin/pending-reviews
    DB-->>Admin: [{repo, confidence_score, score_breakdown}]
    Admin->>Admin: 人工检查低分项目摘要
    alt 审核通过
        Admin->>DB: POST /admin/reviews/{id}/approve
        DB->>DB: review_status = "approved"
    else 审核拒绝
        Admin->>DB: POST /admin/reviews/{id}/reject
        DB->>DB: review_status = "rejected"
    end

    Note over Scheduler, Publisher: ── 周一 10:00 自动发布 ──

    Scheduler->>Publisher: 触发发布 (cron: mon 10:00)
    Publisher->>DB: SELECT repos WHERE review_status="approved" AND published=false
    Publisher->>DB: INSERT INTO weekly_reports (published=true, published_at=now())
    Publisher->>Publisher: FCM 推送通知（可选）
```

---

### 5. 不明确项与假设

| # | 问题 | 假设/决策 |
|---|------|----------|
| 1 | VPS 选型 | **假设**：使用 Hetzner CX22（€4.5/月，2vCPU/4GB/40GB）或阿里云 ECS，用户自行决定 |
| 2 | 域名 | **假设**：`devpulse.app` 已注册，使用 Cloudflare DNS 管理 |
| 3 | LLM 月度预算 | **假设**：$50/月硬上限，在 config 中通过 `LLM_MONTHLY_BUDGET` 环境变量控制 |
| 4 | Firebase Admin SDK | **假设**：使用现有 FCM 集成，不升级完整 Firebase Admin SDK（0.3.1 scope 内仅 Sentry） |
| 5 | 鸿蒙同步更新 | **假设**：鸿蒙端使用 WebView 加载 React SPA，功能自动跟随前端更新，无需单独适配 |
| 6 | Google Play 账号 | **假设**：`$25` 注册费已支付，账号已就绪（0.4.0 发布前需确认） |
| 7 | Product Hunt 物料 | **假设**：由 PM/运营团队在 0.4.0 发布前 2 周准备，不纳入开发任务 |
| 8 | 推荐引擎数据量 | **假设**：初期 <1000 用户，以 L3 热门 + L2 内容过滤为主，L1 协同过滤作为渐进增强 |
| 9 | 分享图语言 | **假设**：分享图使用当前 i18n 语言渲染，支持中/英/日 |

---

## Part B: 任务分解

---

### 6. 依赖包清单

#### Python (requirements-docker.txt 新增)

```
sentry-sdk[fastapi]>=2.0.0,<3.0.0    # Sentry 错误追踪（后端）
scikit-learn>=1.5.0,<1.7.0           # 协同过滤推荐引擎
Pillow>=10.0.0,<12.0.0               # 分享图生成
```

#### npm (package.json 新增)

```
@sentry/react@^8.0.0                         # Sentry 错误追踪（前端）
@sentry/vite-plugin@^2.0.0                   # Sentry Vite 构建插件
react-i18next@^14.0.0                        # React i18n 集成
i18next@^23.0.0                              # i18n 核心库
i18next-browser-languagedetector@^7.0.0      # 浏览器语言检测
vite-plugin-pwa@^0.20.0                      # PWA Service Worker 生成
workbox-precaching@^7.0.0                    # Workbox 预缓存
```

---

### 7. 任务列表（≤5 个任务，按实现顺序）

---

#### T01: 项目基础设施 — 生产部署 + 内容品控

| 维度 | 内容 |
|------|------|
| **Task ID** | T01 |
| **覆盖版本** | 0.3.1 + 0.3.2 |
| **优先级** | P0 |
| **描述** | 建立生产环境基础设施（Nginx/Docker/Sentry/环境变量），同时实现 LLM 摘要置信度评分和审核端点。两者合并是因为：部署后才能验证审核端点在生产环境的正确性，且 models.py 需同时变更。 |
| **依赖** | 无（可直接开始） |
| **涉及文件** | |

**后端（8 个文件）**：

- `backend/nginx/nginx.conf` **(NEW)** — Nginx 主配置
- `backend/nginx/conf.d/default.conf` **(NEW)** — 站点配置
- `backend/nginx/conf.d/ssl.conf` **(NEW)** — SSL 模板
- `docker-compose.prod.yml` **(NEW)** — 生产 Docker Compose
- `.env.production.example` **(NEW)** — 环境变量模板
- `backend/devpulse/config.py` **(MODIFY)** — 新增 SENTRY_DSN/ENVIRONMENT
- `backend/devpulse/core/models.py` **(MODIFY)** — Repository 新增 confidence_score/review_status
- `backend/devpulse/api/endpoints/admin.py` **(NEW)** — 审核端点
- `backend/devpulse/services/content_quality.py` **(NEW)** — 置信度评分服务
- `backend/devpulse/services/scheduler.py` **(MODIFY)** — 周一 09:00/10:00 定时任务
- `backend/devpulse/services/storage.py` **(MODIFY)** — crawl 后计算 confidence_score
- `backend/requirements-docker.txt` **(MODIFY)** — 新增 sentry-sdk/pillow
- `backend/Dockerfile` **(MODIFY)** — 构建优化 + sentry init

**前端（4 个文件）**：

- `desktop/src/main.tsx` **(MODIFY)** — Sentry 初始化
- `desktop/vite.config.ts` **(MODIFY)** — 环境变量注入
- `desktop/package.json` **(MODIFY)** — 新增 @sentry/react

**验收标准**：

- `curl https://api.devpulse.app/health` → 200 OK
- Sentry Dashboard 可见前后端异常上报
- 爬取完成后每个项目有 `confidence_score` 字段（0-1）
- `GET /admin/pending-reviews` 返回低分项目列表
- APScheduler 周一 09:00 触发爬取 → 日志可查

---

#### T02: 用户互动 + AI 推荐

| 维度 | 内容 |
|------|------|
| **Task ID** | T02 |
| **覆盖版本** | 0.3.3 + 0.3.4 |
| **优先级** | P1 |
| **描述** | 实现评论/点赞/分享三大互动功能，同时构建推荐引擎。评论和点赞共用 UserBehavior 数据写入逻辑，而推荐引擎直接消费 UserBehavior 数据——两者共享数据模型，合并开发避免接口不兼容。 |
| **依赖** | T01（依赖 models.py 基础，依赖生产 API 可用） |
| **涉及文件** | |

**后端（5 个文件）**：

- `backend/devpulse/core/models.py` **(MODIFY)** — 新增 Comment/Like/UserBehavior 模型
- `backend/devpulse/api/endpoints/interactions.py` **(NEW)** — 评论/点赞/分享端点
- `backend/devpulse/api/endpoints/recommendations.py` **(NEW)** — 推荐端点
- `backend/devpulse/services/interaction_service.py` **(NEW)** — 互动统计
- `backend/devpulse/services/share_image.py` **(NEW)** — Pillow 分享图生成
- `backend/devpulse/services/recommendation.py` **(NEW)** — 推荐引擎（三层降级）
- `backend/requirements-docker.txt` **(MODIFY)** — 新增 scikit-learn

**前端（6 个文件）**：

- `desktop/src/pages/RepoDetailPage.tsx` **(MODIFY)** — 集成评论区+点赞+分享
- `desktop/src/components/CommentSection.tsx` **(NEW)** — 评论区组件
- `desktop/src/components/ShareMenu.tsx` **(NEW)** — 分享菜单
- `desktop/src/pages/TrendingPage.tsx` **(MODIFY)** — 新增"为你推荐"Tab
- `desktop/src/components/RecommendationList.tsx` **(NEW)** — 推荐列表
- `desktop/src/stores/useInteractionStore.ts` **(NEW)** — 互动状态
- `desktop/src/stores/useRecommendationStore.ts` **(NEW)** — 推荐状态
- `desktop/src/types/index.ts` **(MODIFY)** — 新增类型

**验收标准**：

- 详情页底部可见评论列表 → 发表评论 → 实时刷新
- 点击 👍 → 数字 +1 → 二次点击取消
- 分享按钮 → 可复制链接 / 下载分享图（1200×630 PNG）
- 浏览 3 个项目后 → "为你推荐"展示相关仓库
- 新用户（零行为）→ "为你推荐"展示全局热门

---

#### T03: 性能优化 + PWA + CDN

| 维度 | 内容 |
|------|------|
| **Task ID** | T03 |
| **覆盖版本** | 0.3.5 |
| **优先级** | P1 |
| **描述** | 前端性能优化（代码分割 + 懒加载）、PWA Service Worker 集成、Nginx brotli 压缩配置、Cloudflare CDN 部署指南。三项优化均在构建和部署层面，互相关联（PWA SW 依赖正确的构建输出，CDN 依赖 Nginx 静态文件服务）。 |
| **依赖** | T01（依赖 Nginx 部署 + vite.config.ts 基础） |
| **涉及文件** | |

**前端（5 个文件）**：

- `desktop/vite.config.ts` **(MODIFY)** — manualChunks + vite-plugin-pwa
- `desktop/src/App.tsx` **(MODIFY)** — React.lazy() + Suspense 路由分割
- `desktop/public/manifest.json` **(NEW)** — PWA manifest
- `desktop/public/offline.html` **(NEW)** — 离线回退页
- `desktop/src/components/ImageWithLazy.tsx` **(NEW)** — 图片懒加载
- `desktop/package.json` **(MODIFY)** — 新增 vite-plugin-pwa/workbox

**部署配置（3 个文件）**：

- `backend/nginx/conf.d/gzip.conf` **(NEW)** — brotli/gzip 压缩配置
- `backend/nginx/conf.d/default.conf` **(MODIFY)** — 静态资源缓存头

**验收标准**：

- Lighthouse Performance ≥ 90
- LCP < 1.5s
- 首屏 JS < 200KB（gzip 后）
- 离线状态下打开 App → 展示上次缓存数据 + "离线模式"标签
- `curl -H "Accept-Encoding: br"` → 返回 brotli 压缩内容

---

#### T04: 管理后台 + i18n + SEO

| 维度 | 内容 |
|------|------|
| **Task ID** | T04 |
| **覆盖版本** | 0.3.6 + 0.3.7 |
| **优先级** | P1 |
| **描述** | 实现 Admin 管理后台（Dashboard 看板 + 用户管理 + 爬虫触发），同时完成 i18n 三语翻译和 SEO 基础。两者合并是因为：Admin 页面本身需要 i18n，且 Layout 组件的导航栏变更需同时考虑 Admin 入口和 LanguageSwitcher。 |
| **依赖** | T02（依赖 User 模型 role 字段，依赖评论/点赞数据展示在看板中） |
| **涉及文件** | |

**后端（5 个文件）**：

- `backend/devpulse/core/models.py` **(MODIFY)** — User 新增 role/is_active；新增 DailyStats
- `backend/devpulse/api/endpoints/admin.py` **(MODIFY)** — Dashboard + 用户管理 + 爬虫触发
- `backend/devpulse/api/dependencies.py` **(MODIFY)** — require_admin 依赖
- `backend/devpulse/services/admin_service.py` **(NEW)** — 统计聚合
- `backend/devpulse/api/endpoints/seo.py` **(NEW)** — sitemap.xml
- `backend/devpulse/main.py` **(MODIFY)** — 注册路由

**前端（17 个文件）**：

- `desktop/src/pages/AdminPage.tsx` **(NEW)** — 管理后台
- `desktop/src/components/admin/DashboardCards.tsx` **(NEW)** — 看板卡片
- `desktop/src/components/admin/UserManagement.tsx` **(NEW)** — 用户管理
- `desktop/src/components/admin/AdminCharts.tsx` **(NEW)** — 管理图表
- `desktop/src/components/Layout.tsx` **(MODIFY)** — Admin 入口 + LanguageSwitcher
- `desktop/src/i18n.ts` **(NEW)** — i18next 初始化
- `desktop/src/locales/zh/*.json` **(NEW × 7)** — 中文翻译
- `desktop/src/locales/en/*.json` **(NEW × 7)** — 英文翻译
- `desktop/src/locales/ja/*.json` **(NEW × 7)** — 日文翻译
- `desktop/src/components/LanguageSwitcher.tsx` **(NEW)** — 语言切换器
- `desktop/src/components/SEOHead.tsx` **(NEW)** — SEO meta 标签
- `desktop/index.html` **(MODIFY)** — lang 属性 + GA4
- `desktop/package.json` **(MODIFY)** — 新增 react-i18next

**验收标准**：

- Admin 登录 → Dashboard 展示 DAU/阅读量/收藏数/LLM 成本
- 用户管理列表 → 封禁/解禁操作即时生效
- 切换语言（中→英→日）→ 全站文案实时更新
- sitemap.xml 可访问，Google Search Console 可索引
- GA4 埋点正常上报

---

#### T05: QA + 正式发布

| 维度 | 内容 |
|------|------|
| **Task ID** | T05 |
| **覆盖版本** | 0.3.8 + 0.4.0 |
| **优先级** | P0 |
| **描述** | 全端回归测试、M6/M8 门禁执行、压力测试、CHANGELOG 编写、版本号统一、商店上架材料准备。这是 Phase 4 的汇总 QA 关卡和发布里程碑。 |
| **依赖** | T01, T02, T03, T04（所有功能完成后才能全量 QA） |
| **涉及文件** | |

- `backend/devpulse/__init__.py` **(MODIFY)** — `__version__ = "0.4.0"`
- `desktop/package.json` **(MODIFY)** — `"version": "0.4.0"`
- `CHANGELOG.md` **(NEW)** — 完整变更日志
- `docs/test-matrix-phase4.md` **(NEW)** — 测试矩阵
- `scripts/benchmark.sh` **(NEW)** — wrk 压测脚本

**验收标准**：

- M6 Reliability Gate 全部通过（回归 + 健康检查）
- M8 Quality Gate 五维审计 0 CRITICAL
- 三端全量回归测试覆盖率 ≥ 80%，通过率 > 95%
- wrk 1000 并发压测无 5xx
- `__version__` 统一为 `"0.4.0"`
- CHANGELOG.md 覆盖 0.3.1→0.4.0 全部变更
- Google Play / AppGallery / Product Hunt 商店上架材料就绪

---

### 8. 共享知识

#### 8.1 生产环境变量模板 (`.env.production.example`)

```bash
# ── 数据库 ──────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://devpulse:CHANGE_ME@postgres:5432/devpulse
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ── JWT 认证 ────────────────────────────────────────
JWT_SECRET_KEY=CHANGE_ME_USE_OPENSSL_RAND_BASE64_64
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=7

# ── Sentry 错误追踪 ──────────────────────────────────
SENTRY_DSN=https://xxx@sentry.io/xxx
ENVIRONMENT=production
DEPLOY_MODE=production

# ── LLM ─────────────────────────────────────────────
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx
LLM_MONTHLY_BUDGET=50.0

# ── Firebase ────────────────────────────────────────
FCM_ENABLED=false
FCM_CREDENTIALS_PATH=/app/firebase-credentials.json

# ── API ─────────────────────────────────────────────
API_BASE_URL=https://api.devpulse.app
CORS_ORIGINS=["https://devpulse.app","capacitor://localhost","https://tauri.localhost"]
```

#### 8.2 Nginx 配置规范

- **SSL**: 使用 Let's Encrypt certbot，证书路径 `/etc/letsencrypt/live/devpulse.app/`
- **反向代理**: `/api/` → `http://devpulse-api:8000/`，去除 `/api` 前缀
- **静态文件**: React build 输出挂载到 `/usr/share/nginx/html`
- **缓存头**: 静态资源 `Cache-Control: public, max-age=31536000, immutable`（带 hash 的文件名）
- **安全头**: `X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff`、`Strict-Transport-Security: max-age=63072000`
- **brotli**: `brotli on; brotli_comp_level 6;` 对 text/html/js/css/svg/json
- **gzip**: `gzip on; gzip_comp_level 5;` 作为 brotli fallback

#### 8.3 PWA 缓存策略

| 资源 | URL 模式 | 策略 | MaxAge | MaxEntries |
|------|---------|------|--------|------------|
| JS/CSS 构建产物 | `/assets/*.js`, `/assets/*.css` | CacheFirst | 30d | 100 |
| 字体 | `*.woff2`, `*.woff` | CacheFirst | 30d | 30 |
| 图片 | `*.png`, `*.jpg`, `*.webp`, `*.svg` | CacheFirst | 7d | 200 |
| Trending API | `/repos/trending*` | NetworkFirst | 5min | 20 |
| Repo Detail API | `/repos/*` (except trending) | NetworkFirst | 1h | 100 |
| SPA Shell | `/index.html` | NetworkFirst | — | 1 |
| 其他 API | `/api/*` | NetworkOnly | — | — |

#### 8.4 i18n Key 命名规范

```
格式: {namespace}.{module}.{component}.{property}

命名空间(7个): common, trending, detail, auth, settings, admin, recommendation

示例:
- common.nav.trending.label        = "Trending"
- common.button.submit.label       = "Submit"
- common.status.loading.text       = "Loading..."
- detail.comment.placeholder.text  = "Write a comment..."
- detail.comment.count.label       = "{{count}} comments"
- recommendation.reason.similar    = "Similar to {{repo}} you starred"
- admin.dashboard.dau.label        = "DAU"

规则:
1. 使用点号分隔，小写+下划线
2. 带参数用 {{param}} 双花括号
3. 复数形式用 i18next 的 count 机制
4. 命名空间对应 `locales/{lang}/{namespace}.json`
```

#### 8.5 通用约定

- 所有 API 响应使用 `{code, message, data}` 格式（保持现有）
- 认证使用 JWT Bearer Token（保持现有）
- 所有日期存储为 ISO 8601 UTC（保持现有）
- Git 提交信息格式：`feat(scope): 说明` / `fix(scope): 说明`
- 前端 API 调用统一经过 `api-client.ts`，自动附加 JWT + 重试 + 缓存
- Admin 端点统一使用 `require_admin` 依赖注入（检查 `role == "admin"`）
- 推荐引擎计算在请求时实时执行（非离线预计算），通过 24h 缓存减轻负载

---

### 9. 任务依赖图

```mermaid
graph TD
    T01["T01: 生产部署 + 内容品控<br/>0.3.1 + 0.3.2<br/>P0 - 基础设施"]
    T02["T02: 用户互动 + AI推荐<br/>0.3.3 + 0.3.4<br/>P1 - 核心功能"]
    T03["T03: 性能优化 + PWA<br/>0.3.5<br/>P1 - 体验优化"]
    T04["T04: 管理后台 + i18n<br/>0.3.6 + 0.3.7<br/>P1 - 运营工具"]
    T05["T05: QA + 正式发布<br/>0.3.8 + 0.4.0<br/>P0 - 质量门禁"]

    T01 --> T02
    T01 --> T03
    T01 --> T04
    T02 --> T04
    T02 --> T05
    T03 --> T05
    T04 --> T05
```

> **并行策略**：T01 完成后，T02、T03、T04 可并行推进。T02 完成后 T04 才能验证管理后台的互动数据展示。全部完成后进入 T05 QA 关卡。

---
