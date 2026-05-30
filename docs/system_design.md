# DevPulse Phase 5 — 系统设计 & 任务分解

> **基线版本**: 0.4.0 → **目标版本**: 0.5.0  
> **编制日期**: 2026-06-30  
> **编制人**: 高见远 (Architect)  
> **设计原则**: Phase 5 纯质量加固，不新增功能代码，仅修复 + 测试 + CI + 门禁

---

## Part A: 系统设计

### 1. 实现方案 & 框架选型

#### 1.1 核心技术挑战

| 挑战 | 分析 | 决策 |
|------|------|------|
| 后端测试数据库选型 | SQLite `:memory:` vs testcontainers-python (PostgreSQL)。现有 `database.py` 已支持 SQLite/PostgreSQL 双引擎，且模型中的 `JSON` 列由 SQLAlchemy 自动映射为 SQLite TEXT。无 PostgreSQL 专有语法依赖。 | **SQLite `:memory:`** — 零配置、高速、CI 友好 |
| 前端测试框架 | 项目未安装任何测试框架。需要组件渲染测试 (React 18) + Store 逻辑测试 (Zustand 5)。 | **Vitest + React Testing Library + jsdom** — Vite 原生集成 |
| 前端 API Mock 策略 | Store 依赖 `api-client.ts` (478 行) 发请求。测试不能依赖真实后端。 | **Store 层直接 mock `api-client.ts` 模块**（不引入 MSW 以降低复杂度，MSW 留给 E2E） |
| CI PostgreSQL Service | test.yml 后端 test job 需要 PostgreSQL 跑集成测试（验证 asyncpg 路径）。但同时需保持 SQLite 快速路径。 | **CI 双模式**: PG service container 用于兼容性验证，本地默认 SQLite `:memory:` |
| Docker 构建修复 | `requirements-docker.txt` 缺 `numpy`（scikit-learn 强依赖）。 | 追加 `numpy>=1.24.0,<2.0.0` |
| 性能压测工具 | 需要 HTTP 压测工具，支持高并发、低延迟测量。 | **wrk** — 高性能、Lua 脚本可编程 |

#### 1.2 框架与库选择

**后端测试栈：**

| 库 | 版本 | 用途 | 状态 |
|----|------|------|------|
| `pytest` | `>=8.3.0,<8.4.0` | 测试执行器 | ✅ 已在 `pyproject.toml [dev]` |
| `pytest-asyncio` | `>=0.24.0,<0.25.0` | async 测试支持 | ✅ 已在 `pyproject.toml [dev]` |
| `pytest-cov` | `>=6.0.0,<6.1.0` | 覆盖率报告 | ✅ 已在 `pyproject.toml [dev]` |
| `httpx` | `>=0.28.0,<0.29.0` | Async HTTP 客户端 (用于 ASGI transport) | ✅ 已在核心依赖 |
| `passlib[bcrypt]` | `>=1.7.4` | 密码哈希（通过 `requirements-docker.txt` 已有） | ✅ 间接依赖 |

**前端测试栈：**

| 库 | 版本 | 用途 | 状态 |
|----|------|------|------|
| `vitest` | `^2.1.0` | 测试运行器 | 🆕 需安装 |
| `@testing-library/react` | `^16.0.0` | React 组件渲染测试 | 🆕 需安装 |
| `@testing-library/jest-dom` | `^6.6.0` | DOM 断言匹配器 | 🆕 需安装 |
| `@testing-library/user-event` | `^14.5.0` | 用户交互模拟 | 🆕 需安装 |
| `jsdom` | `^25.0.0` | DOM 环境模拟 | 🆕 需安装 |

**前端不需要 MSW**（理由：Store 测试直接 mock `api-client.ts`，组件测试直接 mock Store hook。MSW 留给 0.4.6 Playwright E2E）。

#### 1.3 架构模式

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 5 测试架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  tests/conftest.py ─── 全局 Fixtures ───────────────────┐  │
│  ├── async_client: AsyncClient (httpx.ASGITransport)     │  │
│  ├── test_db: Database (SQLite :memory:)                 │  │
│  ├── auth_headers: {"Authorization": "Bearer <token>"}   │  │
│  └── seed_*: 预置测试数据                                  │  │
│                                                          │  │
│  tests/factories.py ─── 数据工厂 ────────────────────────│  │
│  ├── create_user(session, **kwargs) → User               │  │
│  ├── create_repo(session, **kwargs) → Repository         │  │
│  ├── create_comment(session, **kwargs) → Comment         │  │
│  └── create_like(session, **kwargs) → Like               │  │
│                                                          │  │
│  tests/test_*.py ─── 按模块分组测试 ─────────────────────◄┘  │
│                                                             │
│  desktop/src/__tests__/ ─── 前端测试 ────────────────────┐  │
│  ├── setup.ts ─── jsdom + mocks 初始化                    │  │
│  ├── components/ ─── 组件渲染测试                          │  │
│  ├── stores/ ─── Store action/selector 测试               │  │
│  ├── pages/ ─── 页面级渲染测试                             │  │
│  └── utils/ ─── 工具函数测试                               │  │
│                                                          │  │
│  e2e/ ─── Playwright E2E (0.4.6) ────────────────────────◄┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. 文件列表（按版本标注）

> 标记说明: `[N]` = 新增文件, `[M]` = 修改文件, `[V]` = 所属版本

#### 2.1 后端文件

| 文件路径 | 操作 | 版本 | 说明 |
|---------|------|------|------|
| `backend/requirements-docker.txt` | [M] | 0.4.1 | 追加 `numpy` |
| `backend/devpulse/config.py` | [M] | 0.4.1 | `API_BASE_URL` 已有（line 89），无需修改。仅确认配置项存在 |
| `backend/devpulse/api/endpoints/seo.py` | [M] | 0.4.1 | 第 24 行：`base_url` 从硬编码改为 `settings.API_BASE_URL or "https://devpulse.app"` |
| `tests/__init__.py` | [N] | 0.4.1/0.4.2 | 包标记 |
| `tests/conftest.py` | [N] | 0.4.1/0.4.2 | 全局 fixtures |
| `tests/factories.py` | [N] | 0.4.2 | 测试数据工厂 |
| `tests/test_auth.py` | [N] | 0.4.2 | M1: 8 用例 |
| `tests/test_trending.py` | [N] | 0.4.2 | M2: 6 用例 |
| `tests/test_collections.py` | [N] | 0.4.2 | M3: 5 用例 |
| `tests/test_interaction.py` | [N] | 0.4.2 | M4: 11 用例 |
| `tests/test_recommendation.py` | [N] | 0.4.2 | M5: 4 用例 |
| `tests/test_admin.py` | [N] | 0.4.2 | M7: 8 用例 |
| `tests/test_seo.py` | [N] | 0.4.2 | M8: 2 用例 (sitemap + i18n 后端部分) |
| `tests/test_health.py` | [N] | 0.4.2 | M6/M9: health + 基础 |

> 合计：57 测试用例覆盖 M1-M9（详见 `test-matrix-phase4.md`）

#### 2.2 前端文件

| 文件路径 | 操作 | 版本 | 说明 |
|---------|------|------|------|
| `desktop/src/components/Layout.tsx` | [M] | 0.4.1 | 导入并挂载 `LanguageSwitcher` |
| `desktop/vitest.config.ts` | [N] | 0.4.3 | Vitest 配置 |
| `desktop/src/__tests__/setup.ts` | [N] | 0.4.3 | jsdom + 全局 mock |
| `desktop/src/__tests__/components/CommentSection.test.tsx` | [N] | 0.4.3 | P0-9 组件渲染测试 |
| `desktop/src/__tests__/components/LanguageSwitcher.test.tsx` | [N] | 0.4.3 | P0-9 组件渲染测试 |
| `desktop/src/__tests__/stores/useInteractionStore.test.ts` | [N] | 0.4.3 | P0-10 Store 测试 |
| `desktop/src/__tests__/stores/useRecommendationStore.test.ts` | [N] | 0.4.3 | P0-10 Store 测试 |
| `desktop/src/__tests__/stores/useAdminStore.test.ts` | [N] | 0.4.3 | P0-10 Store 测试 |
| `desktop/src/__tests__/pages/TrendingPage.test.tsx` | [N] | 0.4.3 | P1-1 页面测试 |
| `desktop/src/__tests__/pages/RepoDetailPage.test.tsx` | [N] | 0.4.3 | P1-1 页面测试 |
| `desktop/src/__tests__/pages/AdminPage.test.tsx` | [N] | 0.4.3 | P1-1 页面测试 |
| `desktop/src/__tests__/utils/i18n.test.ts` | [N] | 0.4.3 | P1-2 i18n 测试 |

#### 2.3 CI 文件

| 文件路径 | 操作 | 版本 | 说明 |
|---------|------|------|------|
| `.github/workflows/test.yml` | [M] | 0.4.4 | 去 `continue-on-error`，加 PG service container |
| `.github/workflows/lint.yml` | [M] | 0.4.4 | 确认后端 test 步骤存在（当前仅有 lint + typecheck） |

#### 2.4 文档文件

| 文件路径 | 操作 | 版本 | 说明 |
|---------|------|------|------|
| `ARCHITECTURE.md` | [M] | 0.4.1 | 更新目录结构描述 |
| `docs/perf-report-0.5.0.md` | [N] | 0.4.5 | 性能压测报告 |
| `e2e/` 目录 | [N] | 0.4.6 | Playwright E2E (5 用例) |
| `docs/gate-m6-0.5.0.md` | [N] | 0.5.0 | M6 门禁报告 |
| `docs/gate-m8-0.5.0.md` | [N] | 0.5.0 | M8 门禁报告 |
| `CHANGELOG.md` | [M] | 0.5.0 | 追加 v0.5.0 |
| `docs/release_notes_0.5.0.md` | [N] | 0.5.0 | 发布说明 |
| `README.md` | [M] | 0.5.0 | 更新徽章（P2-4） |

#### 2.5 E2E 文件 (0.4.6)

| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `e2e/package.json` | [N] | Playwright 项目配置 |
| `e2e/playwright.config.ts` | [N] | Playwright 配置 |
| `e2e/tests/happy-path.spec.ts` | [N] | P1-6: 注册→浏览→点赞→评论 |
| `e2e/tests/i18n.spec.ts` | [N] | P1-7: 语言切换验证 |
| `e2e/tests/admin.spec.ts` | [N] | P1-8: 登录→Dashboard→审核→封禁 |
| `e2e/tests/pwa.spec.ts` | [N] | P2-2: 离线访问（P2） |
| `e2e/tests/auth-gate.spec.ts` | [N] | P2-3: 未登录→登录→返回（P2） |

---

### 3. 数据结构和接口

#### 3.1 后端测试 Fixtures 设计 (conftest.py)

```mermaid
classDiagram
    class TestFixtures {
        +async_client() AsyncClient
        +test_db() Database
        +auth_headers(async_client, test_db) dict
        +admin_headers(async_client, test_db) dict
        +seed_repos(test_db) list~Repository~
        +seed_users(test_db) tuple~User, User~
    }

    class AsyncClient {
        +get(url, headers) Response
        +post(url, json, headers) Response
        +put(url, json, headers) Response
        +delete(url, headers) Response
    }

    class Database {
        +create_tables()
        +drop_tables()
        +get_session() AsyncSession
        +close()
    }

    class FactoryFunctions {
        +create_user(session, email, password, role, is_active) User
        +create_repo(session, full_name, language, source, total_stars, trending_rank, trending_since, review_status) Repository
        +create_comment(session, user_id, repo_id, content, parent_id) Comment
        +create_like(session, user_id, repo_id) Like
        +create_favorite(session, user_id, repo_id) Favorite
        +create_user_behavior(session, user_id, repo_id, action_type) UserBehavior
    }

    TestFixtures --> AsyncClient : produces
    TestFixtures --> Database : produces
    FactoryFunctions --> Database : uses AsyncSession
```

#### 3.2 后端 conftest.py 接口定义

```python
# tests/conftest.py — 全局 Fixtures

@pytest.fixture(scope="session")  # 或 function
def app():
    """创建 FastAPI app 实例，注册所有路由，返回 app 对象"""
    ...

@pytest.fixture
async def test_db():
    """创建 SQLite :memory: Database 实例，create_tables，yield，drop_tables"""
    ...

@pytest.fixture
async def async_client(app, test_db):
    """httpx.AsyncClient(app=app, base_url="http://test")，注入 test_db 到 app.state"""
    ...

@pytest.fixture
async def auth_headers(async_client, test_db):
    """注册用户 → 登录 → 返回 {"Authorization": "Bearer <access_token>"}"""
    ...

@pytest.fixture
async def admin_headers(async_client, test_db):
    """注册 admin 用户 → 返回 admin auth headers"""
    ...
```

#### 3.3 后端 factories.py 接口定义

```python
# tests/factories.py — 测试数据工厂

async def create_user(session, *, email="test@example.com", password="Test1234",
                       role="user", is_active=True, display_name=None) -> User:
    """创建并返回 User，自动 bcrypt 哈希密码"""
    ...

async def create_repo(session, *, full_name="owner/repo", language="Python",
                       source="github", total_stars=1000, trending_rank=1,
                       trending_since="weekly", review_status="approved",
                       description=None, topics=None) -> Repository:
    """创建并返回 Repository"""
    ...

async def create_comment(session, *, user_id, repo_id, content="Great!",
                          parent_id=None) -> Comment:
    """创建并返回 Comment"""
    ...

async def create_like(session, *, user_id, repo_id) -> Like:
    """创建并返回 Like"""
    ...

async def create_favorite(session, *, user_id, repo_id) -> Favorite:
    """创建并返回 Favorite"""
    ...
```

#### 3.4 前端 vitest.config.ts 设计

```typescript
// desktop/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/__tests__/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

#### 3.5 前端 setup.ts 设计

```typescript
// desktop/src/__tests__/setup.ts
import '@testing-library/jest-dom';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key, i18n: { language: 'zh', changeLanguage: vi.fn() } }),
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useParams: () => ({}), useNavigate: () => vi.fn() };
});

// Mock zustand stores selectively
vi.mock('../../stores/useAuthStore', () => ({ useAuthStore: vi.fn() }));
```

---

### 4. 程序调用流程

#### 4.1 后端测试执行流程

```mermaid
sequenceDiagram
    participant P as pytest runner
    participant CF as conftest.py
    participant DB as Database(SQLite :memory:)
    participant APP as FastAPI app
    participant TC as Test Case
    participant EP as API Endpoint

    P->>CF: 收集 fixtures
    CF->>DB: create_tables()
    DB-->>CF: tables ready
    CF->>APP: 创建 app 实例
    CF->>APP: app.state.db = test_db
    CF-->>P: fixtures ready

    P->>TC: 执行 test_register_success
    TC->>APP: POST /auth/register via async_client
    APP->>DB: get_session() → insert User
    DB-->>APP: user created
    APP-->>TC: 201 {access_token, ...}
    TC->>TC: assert response.status_code == 201
    TC->>TC: assert "access_token" in response.json()

    P->>TC: 执行 test_register_duplicate
    TC->>APP: POST /auth/register (same email)
    APP->>DB: SELECT User WHERE email
    DB-->>APP: existing user found
    APP-->>TC: 409 {"detail": "该邮箱已被注册"}
    TC->>TC: assert response.status_code == 409

    Note over P,DB: 所有 57 用例执行完毕后
    P->>CF: teardown
    CF->>DB: drop_tables()
    CF->>DB: close()
```

#### 4.2 前端测试执行流程

```mermaid
sequenceDiagram
    participant V as Vitest runner
    participant SU as setup.ts
    participant CT as Component Test
    participant C as React Component
    participant S as Zustand Store
    participant M as Mock Modules

    V->>SU: 加载 setup.ts
    SU->>M: 注册全局 mock (i18next, react-router-dom)
    M-->>SU: mocks ready
    SU-->>V: setup complete

    V->>CT: LanguageSwitcher 渲染测试
    CT->>C: render(<LanguageSwitcher />)
    C->>S: useAuthStore() → mock data
    S-->>C: { user: { language: 'zh' } }
    C-->>CT: DOM 输出
    CT->>CT: expect(screen.getByText('ZH')).toBeInTheDocument()

    V->>CT: Store 测试 - useInteractionStore
    CT->>S: store.getState().fetchComments('owner/repo')
    S->>M: api-client.ts mock → { code: 0, data: {...} }
    M-->>S: mock response
    S-->>CT: state 更新
    CT->>CT: expect(store.getState().comments).toHaveLength(3)
```

#### 4.3 CI 流水线执行流程

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant L as Lint Job
    participant T as Test Job
    participant BE as Backend Test
    participant FE as Frontend Test
    participant PG as PostgreSQL Container
    participant R as Release Job

    GH->>L: lint.yml → Ruff + Pyright
    L-->>GH: ✅ / ❌

    GH->>T: test.yml
    par Backend Test
        T->>PG: 启动 postgres:16-alpine
        T->>BE: pip install -e ".[dev]"
        BE->>PG: 连接验证
        T->>BE: pytest tests/ --cov=devpulse --cov-report=xml
        BE-->>T: 覆盖率报告
    and Frontend Test
        T->>FE: pnpm install --frozen-lockfile
        T->>FE: pnpm test (无 continue-on-error!)
        FE-->>T: pass / fail
    end
    T-->>GH: ✅ (仅当两者都通过)

    GH->>R: release.yml (on tag push)
    R-->>GH: Docker build + push
```

---

### 5. 待明确事项 (Anything UNCLEAR)

| # | 事项 | 假设 / 建议 | 影响 |
|---|------|------------|------|
| 1 | `backend/setup.py` 是否存在？`pip install -e ".[dev]"` 需 `pyproject.toml` 或 `setup.py`。 | 已确认 `pyproject.toml` 存在且含 `[project.optional-dependencies] dev`。`pip install -e ".[dev]"` 可用。 | 无风险 |
| 2 | 前端 Store 中调用的 `api-client.ts` 函数签名是否稳定？ | 假设现有 478 行 `api-client.ts` 的函数签名在测试中保持不变。如果函数签名变了，mock 也需同步更新。 | 低风险 |
| 3 | Playwright E2E 的目标浏览器环境？ | 假设仅测 Desktop Web (Chromium)。移动端 WebView 留给 v1.0.0。 | CI 安装 `playwright chromium` 即可 |
| 4 | M6/M8 门禁模板由谁设计？ | PRD 建议 David (架构师) 设计模板。**本设计文档产出模板大纲**（见下文 Shared Knowledge），由 QA 执行。 | 需确认团队分工 |
| 5 | `wrk` 压测结果的不稳定性如何处理？ | 手动执行 + 取 3 次平均值。不集成到 CI。结果归档到 `docs/perf-report-0.5.0.md`。 | 无风险 |
| 6 | `tests/__init__.py` 和 `conftest.py` 属于 0.4.1 还是 0.4.2？ | 建议挂 0.4.1（创建目录骨架 + conftest.py 基础 fixtures），0.4.2 填充完整测试用例。 | 无影响 |

---

## Part B: 任务分解

### 6. 依赖包清单

#### 6.1 Backend (Python)

| 包名 | 版本约束 | 类型 | 操作 | 版本 |
|------|---------|------|------|------|
| `pytest` | `>=8.3.0,<8.4.0` | dev | 已有，无需操作 | — |
| `pytest-asyncio` | `>=0.24.0,<0.25.0` | dev | 已有，无需操作 | — |
| `pytest-cov` | `>=6.0.0,<6.1.0` | dev | 已有，无需操作 | — |
| `httpx` | `>=0.28.0,<0.29.0` | prod | 已有，无需操作 | — |
| `numpy` | `>=1.24.0,<2.0.0` | prod (docker) | 🆕 追加到 `requirements-docker.txt` | 0.4.1 |

#### 6.2 Frontend (Node.js)

| 包名 | 版本约束 | 类型 | 操作 | 版本 |
|------|---------|------|------|------|
| `vitest` | `^2.1.0` | devDependency | 🆕 安装 | 0.4.3 |
| `@testing-library/react` | `^16.0.0` | devDependency | 🆕 安装 | 0.4.3 |
| `@testing-library/jest-dom` | `^6.6.0` | devDependency | 🆕 安装 | 0.4.3 |
| `@testing-library/user-event` | `^14.5.0` | devDependency | 🆕 安装 | 0.4.3 |
| `jsdom` | `^25.0.0` | devDependency | 🆕 安装 | 0.4.3 |
| `@vitest/coverage-v8` | `^2.1.0` | devDependency | 🆕 安装（P2-1 覆盖率） | 0.4.3 |

#### 6.3 E2E (0.4.6)

| 包名 | 版本约束 | 类型 | 操作 |
|------|---------|------|------|
| `@playwright/test` | `^1.48.0` | devDependency | 🆕 安装 |
| `playwright` | `^1.48.0` | devDependency | 🆕 安装（已在 backend 核心依赖中，但那是 Python 版本） |

---

### 7. 任务列表（按实现顺序，≤5 个任务）

#### T01: 项目基础设施 (0.4.1 BugFix)

| 维度 | 内容 |
|------|------|
| **Task ID** | T01 |
| **任务名称** | 项目基础设施：修复 6 个已知缺陷 + 测试骨架搭建 |
| **源文件** | `backend/requirements-docker.txt` [M], `backend/devpulse/api/endpoints/seo.py` [M], `desktop/src/components/Layout.tsx` [M], `ARCHITECTURE.md` [M], `tests/__init__.py` [N], `tests/conftest.py` [N] |
| **依赖** | 无 |
| **优先级** | P0 |
| **所属版本** | 0.4.1 |
| **说明** | 1) 修复 `requirements-docker.txt` 缺少 `numpy`；2) 修复 `seo.py` base_url 硬编码；3) 修复 `Layout.tsx` 导入 LanguageSwitcher；4) 修复 `ARCHITECTURE.md` 目录结构；5) 创建 `tests/` 目录骨架 + `conftest.py` 基础 fixtures；6) `tests/__init__.py` |

#### T02: 后端测试实现 (0.4.2)

| 维度 | 内容 |
|------|------|
| **Task ID** | T02 |
| **任务名称** | 后端集成测试：57 个 API 测试用例 (M1-M9) |
| **源文件** | `tests/factories.py` [N], `tests/test_auth.py` [N], `tests/test_trending.py` [N], `tests/test_collections.py` [N], `tests/test_interaction.py` [N], `tests/test_recommendation.py` [N], `tests/test_admin.py` [N], `tests/test_seo.py` [N], `tests/test_health.py` [N], `tests/conftest.py` [M], `backend/devpulse/config.py` [M] |
| **依赖** | T01 |
| **优先级** | P0 |
| **所属版本** | 0.4.2 |
| **说明** | 1) `factories.py` 数据工厂（create_user/create_repo/create_comment/create_like/create_favorite）；2) conftest.py 补充 seed fixtures；3) config.py 新增 `API_BASE_URL` 配置项（已存在 line 89，确认可用）；4) 8 个测试文件覆盖 57 用例，目标覆盖率 ≥80% |

#### T03: 前端测试 + CI 修复 (0.4.3 + 0.4.4)

| 维度 | 内容 |
|------|------|
| **Task ID** | T03 |
| **任务名称** | 前端测试实现 + CI 流水线修复 |
| **源文件** | `desktop/vitest.config.ts` [N], `desktop/src/__tests__/setup.ts` [N], `desktop/src/__tests__/components/CommentSection.test.tsx` [N], `desktop/src/__tests__/components/LanguageSwitcher.test.tsx` [N], `desktop/src/__tests__/stores/useInteractionStore.test.ts` [N], `desktop/src/__tests__/stores/useRecommendationStore.test.ts` [N], `desktop/src/__tests__/stores/useAdminStore.test.ts` [N], `desktop/src/__tests__/pages/TrendingPage.test.tsx` [N], `desktop/src/__tests__/pages/RepoDetailPage.test.tsx` [N], `desktop/src/__tests__/pages/AdminPage.test.tsx` [N], `desktop/src/__tests__/utils/i18n.test.ts` [N], `.github/workflows/test.yml` [M], `.github/workflows/lint.yml` [M], `desktop/package.json` [M] |
| **依赖** | T01 |
| **优先级** | P0 |
| **所属版本** | 0.4.3 + 0.4.4 |
| **说明** | **前端测试 (0.4.3)**: 1) vitest.config.ts + setup.ts 基础设施；2) 2 个组件渲染测试 (CommentSection, LanguageSwitcher)；3) 3 个 Store 逻辑测试；4) 3 个页面测试 (P1)；5) i18n 工具测试 (P1)；6) package.json 加 test script 和 devDependencies。**CI 修复 (0.4.4)**: 1) test.yml 去 `continue-on-error: true`；2) 加 PostgreSQL service container；3) lint.yml 确认流程完整。 |

#### T04: 性能验证 + E2E (0.4.5 + 0.4.6)

| 维度 | 内容 |
|------|------|
| **Task ID** | T04 |
| **任务名称** | 性能压测 + Playwright E2E 关键路径 |
| **源文件** | `docs/perf-report-0.5.0.md` [N], `e2e/package.json` [N], `e2e/playwright.config.ts` [N], `e2e/tests/happy-path.spec.ts` [N], `e2e/tests/i18n.spec.ts` [N], `e2e/tests/admin.spec.ts` [N], `e2e/tests/pwa.spec.ts` [N] (P2), `e2e/tests/auth-gate.spec.ts` [N] (P2) |
| **依赖** | T02, T03 |
| **优先级** | P1 |
| **所属版本** | 0.4.5 + 0.4.6 |
| **说明** | **性能 (0.4.5)**: wrk 压测 3 场景 (health 1000 并发, trending 500 并发, recommended 100 并发)，产出 `perf-report-0.5.0.md`。**E2E (0.4.6)**: Playwright 5 用例 (3 P1 happy-path + 2 P2 PWA/auth-gate)，CI 安装 chromium |

#### T05: Docker 验证 + 质量发布 (0.4.7 + 0.5.0)

| 维度 | 内容 |
|------|------|
| **Task ID** | T05 |
| **任务名称** | Docker 全功能验证 + M6/M8 门禁 + 发布文档 |
| **源文件** | `docs/gate-m6-0.5.0.md` [N], `docs/gate-m8-0.5.0.md` [N], `CHANGELOG.md` [M], `docs/release_notes_0.5.0.md` [N], `README.md` [M], `ARCHITECTURE.md` [M] |
| **依赖** | T01, T02, T03, T04 |
| **优先级** | P1 |
| **所属版本** | 0.4.7 + 0.5.0 |
| **说明** | **Docker (0.4.7)**: `docker-compose up` → 浏览器全功能验证 (Trending/评论/推荐/i18n/Admin)。**发布 (0.5.0)**: 1) M6 可靠性门禁执行报告；2) M8 五维质量审计报告；3) CHANGELOG v0.5.0 条目；4) release_notes_0.5.0.md；5) README 徽章更新；6) git tag v0.5.0 |

---

### 8. 共享知识 (Shared Knowledge)

#### 8.1 通用约定

```
- 所有后端 API 测试使用 httpx.AsyncClient + ASGITransport（不启动真实 HTTP server）
- 测试数据库: SQLite :memory:，每个 test function 前后 create_tables/drop_tables
- 错误处理模式: 后端 API 统一返回 {"detail": "..."} (FastAPI HTTPException 默认格式)
- API 响应格式不一致: /auth/* 返回扁平结构，/repos/* 的 interaction/admin 端返回 {code, data, message}。测试断言根据端点适配
- 日期时间: 所有 datetime 字段以 ISO 8601 UTC 存储，测试断言使用 datetime.now(timezone.utc)
```

#### 8.2 测试命名规范

```
- 文件名: test_<module>.py (后端), <ComponentName>.test.tsx (前端)
- 函数名: test_<action>_<scenario> (如 test_register_success, test_register_duplicate_email)
- 前端: describe('<Component>', () => { it('renders <scenario>', () => {}) })
- Store: describe('useXxxStore', () => { it('handles <action>', () => {}) })
```

#### 8.3 API Base URL 配置约定

```
- seo.py 中 base_url 读取: from devpulse.config import settings; base_url = settings.API_BASE_URL or "https://devpulse.app"
- .env 中可设置: API_BASE_URL=https://devpulse.app
- CI 测试环境不设置此变量，sitemap 测试验证默认 fallback 逻辑
```

#### 8.4 CI 约定

```
- PostgreSQL service container: postgres:16-alpine, POSTGRES_USER=devpulse, POSTGRES_PASSWORD=test, POSTGRES_DB=devpulse_test
- 后端 test job 环境变量: DATABASE_URL=postgresql+asyncpg://devpulse:test@localhost:5432/devpulse_test
- 前端 test job: 必须阻塞 CI（已去 continue-on-error）
- 覆盖率报告: pytest-cov 产出 XML，前端 @vitest/coverage-v8 产出 JSON
```

#### 8.5 M6/M8 门禁模板大纲

**M6 可靠性门禁 (docs/gate-m6-0.5.0.md)**:
```
1. 测试覆盖率 ≥80% (后端 pytest-cov)
2. 所有 P0 测试用例通过 (57/57)
3. CI 三 workflow 全绿 (lint + test + release)
4. Docker 构建验证通过
5. 0 CRITICAL 未修复 Bug
```

**M8 五维质量审计 (docs/gate-m8-0.5.0.md)**:
```
维度 1 - 功能完整性: 57 用例全部通过
维度 2 - 代码质量: Ruff + Pyright + ESLint 零告警
维度 3 - 性能基线: wrk 压测 P99 < 阈值
维度 4 - 安全性: JWT 认证 + 密码强度 + SQL 注入防护验证
维度 5 - 可维护性: ARCHITECTURE.md 同步 + CHANGELOG 更新
```

---

### 9. 任务依赖图

```mermaid
graph TD
    T01["T01: 项目基础设施<br/>0.4.1 BugFix<br/>6 缺陷 + 测试骨架"]
    T02["T02: 后端测试实现<br/>0.4.2<br/>57 用例 + factories"]
    T03["T03: 前端测试 + CI 修复<br/>0.4.3 + 0.4.4<br/>组件/Store/页面测试 + CI"]
    T04["T04: 性能验证 + E2E<br/>0.4.5 + 0.4.6<br/>wrk + Playwright"]
    T05["T05: Docker验证 + 质量发布<br/>0.4.7 + 0.5.0<br/>门禁 + CHANGELOG + tag"]

    T01 --> T02
    T01 --> T03
    T02 --> T04
    T03 --> T04
    T02 --> T05
    T03 --> T05
    T04 --> T05

    style T01 fill:#f9f,stroke:#333
    style T02 fill:#bbf,stroke:#333
    style T03 fill:#bfb,stroke:#333
    style T04 fill:#fbb,stroke:#333
    style T05 fill:#ff9,stroke:#333
```

**并行提示**:
- T02 和 T03 可**并行开发**（前后端测试独立，均仅依赖 T01）
- T04 的 0.4.5 (性能) 仅依赖 T02，可与 0.4.6 (E2E) 并行
- 关键路径: T01 → T02 → T04 → T05（4 跳，可控）

---

> **文档版本**: v1.0 | **下次评审**: Phase 5 收尾时更新
