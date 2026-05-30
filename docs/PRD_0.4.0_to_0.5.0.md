# DevPulse「AI 潮汐」— Phase 5 增量 PRD（0.4.0 → 0.5.0）

> **编制日期**: 2026-06-30  
> **编制依据**: Phase 4 全量代码审计报告（57 测试用例 0/57 执行，测试覆盖率 0%）

---

## 1. 项目信息

| 字段 | 内容 |
|------|------|
| **Language** | 中文 |
| **Programming Language** | Python 3.10+ (FastAPI) + TypeScript (React 18) + Rust (Tauri 2.x) |
| **Project Name** | devpulse |
| **基线版本** | 0.4.0（Phase 4 代码完成，测试覆盖率 0%，CI 假绿灯，6 个已知缺陷） |
| **目标版本** | 0.5.0（测试覆盖 ≥80%，CI 全绿，生产可部署，门禁全通） |
| **原始需求** | Phase 4 写了代码，Phase 5 要证明代码是能用的——不新增功能，纯质量加固 |

---

## 2. 产品定义

### 2.1 Product Goals

1. **可信交付（Trustworthy Delivery）**：所有 API 端点有集成测试覆盖，所有前端关键组件有单元测试覆盖，CI 流水线三 workflow 稳定全绿，前端测试失败必须阻塞 CI。
2. **开箱可用（Works Out of the Box）**：新开发者 `git clone` → `docker-compose up` → 浏览器访问即可看到完整功能（评论、推荐、i18n、管理后台）。
3. **质量证明（Quality Proven）**：M6 可靠性门禁 + M8 五维质量审计正式执行并产出报告，测试覆盖率报告可查，性能压测报告可查。

### 2.2 User Stories

| # | 版本 | User Story |
|---|------|-----------|
| 1 | 0.4.1 | As a **新贡献者**, I want **`docker-compose up` 不出错就能看到管理后台、评论、推荐、i18n 全部功能** so that **不用花时间修环境**。 |
| 2 | 0.4.2 | As a **后端开发者**, I want **每个 API 端点都有集成测试，`pytest` 一把过，覆盖率 ≥80%** so that **重构时不用担心破坏已有功能**。 |
| 3 | 0.4.3 | As a **前端开发者**, I want **关键组件有单元测试覆盖（CommentSection、LanguageSwitcher、AdminPage）** so that **改 UI 不会引入回归**。 |
| 4 | 0.4.4 | As a **项目维护者**, I want **GitHub Actions 三 workflow 全绿，PR 合入有质量保障** so that **可以放心接受外部贡献**。 |
| 5 | 0.4.5 | As a **国际用户**, I want **在导航栏直接切换界面语言（中/英/日）** so that **不用进设置页面就能切换**。 |
| 6 | 0.5.0 | As a **运营负责人**, I want **M6/M8 门禁报告 + 性能压测报告归档可查** so that **版本质量有书面背书**。 |

---

## 3. 技术规范

### 3.1 Requirements Pool

#### P0（Must Have — 不修完无法发布 0.5.0）

| ID | 版本 | 类别 | 需求 | 验收标准 |
|----|------|------|------|---------|
| P0-1 | 0.4.1 | 🔧 BugFix | 修复 `requirements-docker.txt` 缺少 `numpy`，导致 Docker 构建失败（B3） | `docker-compose -f docker-compose.prod.yml build` 成功 |
| P0-2 | 0.4.1 | 🔧 BugFix | 修复 `LanguageSwitcher.tsx` 组件断连——导入并挂载到 `Layout.tsx` 导航栏（B2） | 桌面应用导航栏出现语言切换下拉菜单，三语可切换 |
| P0-3 | 0.4.1 | 🔧 BugFix | 修复 `seo.py` 中 `base_url` 硬编码 `https://devpulse.app`，改为从 `config.API_BASE_URL` 读取（B4） | `curl /seo/sitemap.xml` 返回的 URL 使用 config 中的值 |
| P0-4 | 0.4.1 | 🔧 BugFix | 修复 `test.yml` 前端 test job 的 `continue-on-error: true`，测试失败必须阻塞 CI（B6） | 前端测试失败时 CI 变红 |
| P0-5 | 0.4.1 | 🔧 BugFix | 修复 `tests/` 目录不存在——创建目录结构和 `conftest.py`（B1） | `pytest tests/` 能发现测试（即使最初为空） |
| P0-6 | 0.4.1 | 🔧 BugFix | 修复 `ARCHITECTURE.md` 目录结构描述与实际代码不一致（B5） | 文档中的路径与实际代码一致 |
| P0-7 | 0.4.2 | 🧪 后端测试 | 57 个 API 集成测试全部实现并通过（M1-M9 矩阵全部覆盖） | `pytest tests/ --cov=devpulse` 全绿，覆盖率 ≥80% |
| P0-8 | 0.4.2 | 🧪 后端测试 | `tests/conftest.py` + `tests/factories.py` 测试基础设施搭建 | `pytest` fixtures（async client、test DB、auth headers）正常注入 |
| P0-9 | 0.4.3 | 🧪 前端测试 | 关键组件渲染测试：CommentSection、LanguageSwitcher | Vitest + RTL 组件渲染测试通过 |
| P0-10 | 0.4.3 | 🧪 前端测试 | 关键 Store 逻辑测试：useInteractionStore、useRecommendationStore、useAdminStore | Store action/reducer 测试通过 |
| P0-11 | 0.4.4 | ⚙️ CI | GitHub Actions 三 workflow（lint / test / release）全部通过 | PR 页面显示 ✅ 绿勾 |
| P0-12 | 0.4.4 | ⚙️ CI | 后端 test job 添加 PostgreSQL service container | CI 中 `pytest` 能连接数据库跑集成测试 |

#### P1（Should Have — 应有，显著提升质量信心）

| ID | 版本 | 类别 | 需求 | 验收标准 |
|----|------|------|------|---------|
| P1-1 | 0.4.3 | 🧪 前端测试 | 页面级测试：TrendingPage（三 Tab）、RepoDetailPage（互动区）、AdminPage（三 Tab） | 页面渲染 + 交互测试通过 |
| P1-2 | 0.4.3 | 🧪 前端测试 | 工具模块测试：i18n 初始化 + 语言切换逻辑 | i18n 单元测试通过 |
| P1-3 | 0.4.5 | 📊 性能 | `wrk` 1000 并发 `/health` 压测，0 错误，P99 < 100ms | 压测报告 `docs/perf-report-0.5.0.md` 产出 |
| P1-4 | 0.4.5 | 📊 性能 | `wrk` 500 并发 `/api/v1/repos/trending` 压测，0 5xx | 同上报告 |
| P1-5 | 0.4.5 | 📊 性能 | `wrk` 100 并发 `/api/v1/repos/recommended` 压测，P99 < 2s | 同上报告 |
| P1-6 | 0.4.6 | 🎭 E2E | Playwright 关键路径：注册→浏览→点赞→评论（Happy Path） | E2E 通过 |
| P1-7 | 0.4.6 | 🎭 E2E | Playwright i18n：切换语言→验证全站文案变更 | E2E 通过 |
| P1-8 | 0.4.6 | 🎭 E2E | Playwright Admin：登录→Dashboard→审核→封禁用户 | E2E 通过 |
| P1-9 | 0.4.7 | 🐳 Docker | `docker-compose up` → 浏览器全功能可用（Trending、评论、推荐、i18n、Admin） | 手动验证清单全过 |
| P1-10 | 0.5.0 | 📋 门禁 | M6 可靠性门禁正式执行并产出报告 | `docs/gate-m6-0.5.0.md` 产出，0 CRITICAL |
| P1-11 | 0.5.0 | 📋 门禁 | M8 五维质量审计正式执行并产出报告 | `docs/gate-m8-0.5.0.md` 产出，0 CRITICAL |

#### P2（Nice to Have — 资源允许则做）

| ID | 版本 | 类别 | 需求 | 验收标准 |
|----|------|------|------|---------|
| P2-1 | 0.4.3 | 🧪 前端测试 | 前端测试覆盖率报告集成（类似后端 `pytest-cov`） | `pnpm test --run --coverage` 可产出报告 |
| P2-2 | 0.4.6 | 🎭 E2E | Playwright PWA：离线访问→验证缓存降级 | E2E 通过 |
| P2-3 | 0.4.6 | 🎭 E2E | Playwright Auth 门禁：未登录评论→提示登录→登录→返回继续 | E2E 通过 |
| P2-4 | 0.5.0 | 📝 文档 | `README.md` 更新测试覆盖率徽章 + CI 状态徽章 | 徽章显示绿色 |
| P2-5 | 0.5.0 | 📝 文档 | `CHANGELOG.md` 追加 v0.5.0 条目，`docs/release_notes_0.5.0.md` | 发布说明完整 |

---

### 3.2 UI Design Draft

Phase 5 不涉及新增页面或大范围 UI 改造。唯一的 UI 变更是：**将 LanguageSwitcher 组件集成到 Layout 导航栏**。

#### 现状（Bug）

```
┌──────────────────────────────────────────┐
│  DevPulse「AI 潮汐」     [Settings] [👤]  │  ← LanguageSwitcher 组件未挂载
│  ─────────────────────────────────────── │
│                                          │
│  (导航栏中没有语言切换入口，用户无法切换)     │
│                                          │
└──────────────────────────────────────────┘
```

#### 目标（0.4.1 修复后）

```
┌──────────────────────────────────────────┐
│  DevPulse「AI 潮汐」   🌐 ZH ▼  [⚙️] [👤] │  ← LanguageSwitcher 挂载到导航栏
│  ─────────────────────────────────────── │    位于 Settings 图标左侧
│                                          │
│  点击 🌐 下拉：                           │
│  ┌─────────────┐                        │
│  │ 🇨🇳 中文     │                        │
│  │ 🇬🇧 English  │                        │
│  │ 🇯🇵 日本語   │                        │
│  └─────────────┘                        │
└──────────────────────────────────────────┘
```

#### 实现要点

| 要素 | 说明 |
|------|------|
| 挂载位置 | `desktop/src/components/Layout.tsx` 导航栏右侧，Settings 图标左侧 |
| 组件复用 | 直接导入已有 `LanguageSwitcher.tsx`（35 行，无需修改） |
| 展示形式 | 当前语言简写（如 `ZH`）+ 下拉箭头图标，点击展开下拉菜单 |
| 语言选项 | 中文 (zh) / English (en) / 日本語 (ja)，对应国旗 emoji + 语言名 |
| 交互行为 | 点击选项 → `i18n.changeLanguage()` → 全站文案实时更新 |
| 响应式 | 移动端保持与桌面端一致的导航栏位置 |

---

### 3.3 Open Questions（待确认）

1. **测试数据库选型**：后端集成测试用 SQLite `:memory:` 替代 PostgreSQL。但 Phase 4 某些 SQL 可能使用了 PostgreSQL 特有语法（如 `ARRAY` 类型、`JSONB` 操作符），这些在 SQLite 上会失败。是否需要改为 testcontainers-python 启动真实 PostgreSQL 容器？（建议：先用 SQLite 试跑，遇到不兼容再切 testcontainers）

2. **前端测试 MSW 版本**：MSW v2 与 Vitest 的集成方式有 breaking change（`setupServer` → `http` + `HttpResponse`），当前 `desktop/package.json` 中 MSW 版本需确认。如果尚未安装，建议直接使用 MSW v2 最新版。

3. **CI PostgreSQL Service Container 镜像版本**：`.github/workflows/test.yml` 中需添加 `postgres:16-alpine` service container。DevPulse 生产环境用的是 PostgreSQL 16，CI 应保持一致。

4. **Playwright 浏览器环境**：E2E 测试需要在 CI 中安装 Chromium。GitHub Actions 的 `ubuntu-latest` runner 自带 Chrome，但如果需要测试移动端 viewport（Android Chrome Emulator），可能需要额外配置。Phase 5 是否只测 Desktop Web 端？

5. **性能压测环境**：`wrk` 压测是在开发机上手动执行，还是需要集成到 CI？（建议：手动执行 + 报告归档，不在 CI 中跑压测以避免结果不稳定）

6. **M6/M8 门禁模板**：Phase 4 PRD 定义了 M6/M8 门禁但未产出模板。Phase 5 需要先设计门禁检查清单模板再执行。谁来设计模板？（建议：架构师 David 设计模板，QA 工程师执行）

7. **`backend/setup.py` vs `pyproject.toml`**：当前 CI `lint.yml` 使用 `pip install -e ".[dev]"`，需确认 `backend/` 下存在 `setup.py` 或 `pyproject.toml` 且定义了 `[dev]` extras。如果不存在，需创建或改为 `pip install -r requirements.txt`。

---

## 4. 迭代路线图

```
0.4.0 (基线) ──→ 0.4.1 (BugFix) ──→ 0.4.2 (后端测试) ──→ 0.4.3 (前端测试)
      │              │                    │                    │
      │              ├── 修 6 个缺陷       ├── 57 集成测试       ├── 关键组件测试
      │              ├── 补 numpy 依赖     ├── pytest + httpx    ├── Vitest + RTL
      │              └── 连 LanguageSwitcher└── 目标 80% 覆盖     └── 关键路径

0.4.4 (CI 修复) ←── 0.4.5 (性能验证) ←── 0.4.6 (E2E) ←── 0.4.7 (Docker 验证)
      │                 │                    │                 │
      ├── 去 continue   ├── wrk 压测         ├── Playwright     ├── docker-compose
      ├── 加 PG service  ├── 性能基线报告     ├── 关键路径       └── 全功能验证
      └── 三灯全绿       └── M9 执行          └── 5 用例

0.5.0 (质量发布) ←── 文档同步 + M6/M8 执行 + CHANGELOG + git tag
```

### 迭代依赖

```
0.4.1 (BugFix) ────── 独立，可立即开始
0.4.2 (后端测试) ──── 依赖 0.4.1（修复后的代码才能测试）
0.4.3 (前端测试) ──── 依赖 0.4.1（同上）
0.4.4 (CI 修复) ───── 依赖 0.4.2 + 0.4.3（有测试才能跑 CI）
0.4.5 (性能验证) ──── 依赖 0.4.2（需要后端测试环境就绪）
0.4.6 (E2E) ───────── 依赖 0.4.1-0.4.3（全功能就绪）
0.4.7 (Docker 验证) ─ 依赖 0.4.1（Bug 修完）
0.5.0 (发布) ──────── 依赖全部 0.4.1-0.4.7
```

- **可并行**：0.4.2 和 0.4.3（前后端测试独立）、0.4.5 和 0.4.6
- **关键路径**：0.4.1 → 0.4.2 → 0.4.4 → 0.5.0

---

## 5. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|:---:|------|------|
| 后端测试数据准备复杂（需构造 9 模块场景） | 中 | 延迟 0.4.2 | `factories.py` Factory 模式预建测试数据 |
| scikit-learn + numpy 在 CI 中安装慢 | 中 | CI 时间增加 | `pip cache` + `actions/setup-python` 缓存 |
| Phase 4 代码使用了 PostgreSQL 特有语法，SQLite 不兼容 | 中 | 后端测试需切 testcontainers | 0.4.2 初期先试跑，不兼容则升级方案 |
| 前端组件依赖 MSW mock 不稳定 | 低 | 0.4.3 延迟 | 先从 Store 测试开始（无组件渲染依赖） |
| 现有隐式 Bug 被测试发现 | 中 | 额外修复工作量 | 0.4.1 预留修复空间，Bug 归入 P0 |
| Docker 镜像体积过大导致 CI release 超时 | 低 | 发布延迟 | 多阶段构建已配置，预估 ~200MB |

---

## 6. 与 v1.0.0 GA 的边界

v0.5.0 完成后，DevPulse 将具备：
- ✅ 完整功能代码（Phase 2-4）
- ✅ 后端测试覆盖 ≥80%
- ✅ 前端关键路径测试
- ✅ CI/CD 流水线全绿
- ✅ Docker 生产部署验证
- ✅ M6/M8 门禁报告

以下需求留给 v1.0.0 或后续版本：
- iOS 适配（需 Apple Developer 账号 + Mac 构建环境）
- 真实 VPS 部署 + 域名 + SSL（`devpulse.app` 域名购买）
- 三商店（Google Play / AppGallery / Product Hunt）上架
- Firebase Admin SDK 完整接入（推送通知生产化）
- 付费订阅系统（Stripe/Paddle）
- Discord 社区运营
- 真实用户反馈收集与分析
