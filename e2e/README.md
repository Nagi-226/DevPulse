# DevPulse E2E Tests

Playwright 端到端 (End-to-End) 测试套件，覆盖 DevPulse 关键用户路径。

## 前置条件

### 1. 安装依赖

```bash
cd e2e
pnpm install
# 或
npm install
```

### 2. 安装 Chromium 浏览器

```bash
npx playwright install chromium
```

### 3. 启动服务

测试依赖前后端同时运行：

**终端 1 — 启动后端:**
```bash
cd backend
uvicorn devpulse.main:app --host 0.0.0.0 --port 8000
```

**终端 2 — 启动前端:**
```bash
cd desktop
pnpm dev
# 或
npm run dev
```

### 4. 验证服务

```bash
# 验证后端
curl http://localhost:8000/health

# 验证前端
curl http://localhost:5173
```

## 运行测试

### 运行全部测试

```bash
cd e2e
pnpm test
# 或
npx playwright test
```

### 运行单个测试文件

```bash
npx playwright test tests/happy-path.spec.ts
npx playwright test tests/i18n.spec.ts
npx playwright test tests/admin.spec.ts
npx playwright test tests/pwa.spec.ts
npx playwright test tests/auth-gate.spec.ts
```

### 有头模式 (调试用)

```bash
pnpm test:headed
# 或
npx playwright test --headed
```

### 查看测试报告

```bash
pnpm report
# 或
npx playwright show-report
```

## 测试文件说明

| 文件 | 覆盖路径 | 关键场景 |
|------|---------|---------|
| `happy-path.spec.ts` | 全流程 | 注册 → 浏览 Trending → 查看详情 → 点赞 → 评论 |
| `i18n.spec.ts` | 国际化 | 默认为中文、切换英文/日文、语言持久化 |
| `admin.spec.ts` | 管理后台 | Admin 登录 → Dashboard → 用户管理 → 审核列表 |
| `pwa.spec.ts` | PWA 离线 | 离线访问 / Service Worker 缓存 / 网络恢复 |
| `auth-gate.spec.ts` | 鉴权门控 | 未登录评论 → 跳转登录 → 登录后继续操作 |

## 配置

测试配置文件: `playwright.config.ts`

```typescript
{
  testDir: './tests',       // 测试文件目录
  timeout: 30000,            // 单用例超时 30s
  retries: 1,                // 失败重试 1 次
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
}
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `baseURL` | `http://localhost:5173` | 前端地址 |
| `BACKEND_URL` | `http://localhost:8000` | 后端 API 地址 |

可以通过修改 `playwright.config.ts` 中的 `baseURL` 来指向不同的环境。

## 注意事项

1. **测试数据**: 测试会在每次运行时创建临时用户（带时间戳），不会污染生产数据。
2. **数据库**: 测试依赖 SQLite 数据库 (`devpulse.db`)，确保后端已初始化数据库。
3. **Service Worker**: PWA 测试依赖 Service Worker 注册，建议在 `vite build` 后的生产模式下可获得最准确的 PWA 行为。
4. **Admin 测试**: 新注册用户可能默认非 admin 角色，`admin.spec.ts` 已处理此情况（验证访问控制正常工作）。
5. **选择器策略**: 测试使用多种选择器降级策略（`data-testid` → class 名 → 通用选择器），确保在不同实现下都能适配。

## CI 集成

```yaml
# GitHub Actions 示例
- name: Run E2E tests
  run: |
    cd backend && uvicorn devpulse.main:app --port 8000 &
    cd desktop && pnpm dev &
    sleep 5
    cd e2e && npx playwright test
```

## Troubleshooting

### `playwright: command not found`

```bash
npx playwright install chromium
npx playwright test
```

### `Error: connect ECONNREFUSED 127.0.0.1:5173`

前端未启动，请先在 `desktop/` 目录下执行 `pnpm dev`。

### `Error: connect ECONNREFUSED 127.0.0.1:8000`

后端未启动，请先在 `backend/` 目录下执行 `uvicorn devpulse.main:app --port 8000`。

### 测试超时

- 增加 `playwright.config.ts` 中的 `timeout` 值
- 确认前后端服务均正常运行
- 尝试 `--headed` 模式观察实际页面状态
