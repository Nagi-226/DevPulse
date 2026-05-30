# M6 可靠性门禁报告 — v0.5.0

> **门禁类型**: M6 Reliability Gate (ai-dev-guardrails v3.0)
> **执行日期**: 2026-05-30
> **版本**: 0.5.0 (Quality Hardening)
> **判定**: ✅ **PASS**

---

## 回归验证

| 检查项 | 状态 | 证据 |
|--------|:----:|------|
| 后端测试全绿 (72 tests) | ✅ | `pytest tests/ -v` — 8 测试模块覆盖 auth/trending/collections/interaction/recommendation/admin/seo/health |
| 前端测试全绿 (27 tests) | ✅ | Vitest + React Testing Library — 组件/Store/Hooks 覆盖 |
| E2E 测试全绿 (5 scenarios) | ✅ | Playwright: happy-path, i18n, admin, pwa, auth-gate |
| 2 个路由 Bug 已修复 | ✅ | `main.py` 路由顺序重排 + `repos.py` star-history 移至通配路由之前 |
| CI lint workflow 通过 | ✅ | `.github/workflows/lint.yml` — Ruff + Pyright + ESLint |
| CI test workflow 通过 | ✅ | `.github/workflows/test.yml` — 后端 pytest + 前端 vitest，已移除 `continue-on-error` |
| CI release workflow 可用 | ✅ | `.github/workflows/release.yml` |
| 回退路径明确 | ✅ | `git tag v0.4.0` 基线 → `git checkout v0.4.0` 可回退 |
| 边界用例覆盖 | ✅ | 空状态、错误状态、极限输入已在各测试模块中覆盖 |
| 无副作用扩散 | ✅ | 路由修复仅调整注册顺序，不影响既有端点行为 |

---

## 迭代健康检查

| 检查项 | 状态 | 证据 |
|--------|:----:|------|
| 代码结构清晰，无临时方案残留 | ✅ | BugFix 修复均已合并到正式代码路径，无 `# TEMP` / `# HACK` 注释残留 |
| 无 "以后再重构" 的 TODO | ✅ | 代码库中无 `TODO: refactor` 或 `FIXME` 标记 |
| 所有依赖在 `pyproject.toml` / `package.json` 声明 | ✅ | `numpy` 已补入 `requirements-docker.txt`；bcrypt==4.0.1 / PyJWT==2.7.0 已锁定 |
| 新引入模式与现有模式一致 | ✅ | 测试 conftest 使用 SQLite `:memory:` + httpx ASGITransport，与现有 fixture 风格一致 |
| 2 周后其他人能无痛接手 | ✅ | ARCHITECTURE.md 目录结构已更新；CHANGELOG 详尽记录变更 |

---

## 缺陷修复清单 (0.4.1 → 0.5.0)

| # | 缺陷 | 严重程度 | 修复版本 | 修复方式 |
|---|------|:--------:|:--------:|------|
| 1 | `main.py` repos 通配路由拦截 interaction/recommendation GET 请求 | 🔴 HIGH | 0.4.1 | 调整 router 注册顺序：interaction → recommendation → repos |
| 2 | `repos.py` `GET /{full_name:path}/star-history` 被通配路由拦截 | 🔴 HIGH | 0.4.1 | 将 star-history 路由移至 `/{full_name:path}` 之前 |
| 3 | `numpy` 未在 `requirements-docker.txt` 声明（scikit-learn 依赖） | 🟡 MEDIUM | 0.4.1 | 添加 `numpy` 到 requirements-docker.txt |
| 4 | `seo.py` base_url 硬编码 | 🟡 MEDIUM | 0.4.1 | 改为 `settings.API_BASE_URL` 读取，带 fallback |
| 5 | `LanguageSwitcher` 组件已实现但未渲染 | 🟡 MEDIUM | 0.4.1 | 在 Layout 组件中挂载 LanguageSwitcher |
| 6 | bcrypt 5.0 与 passlib 不兼容 / PyJWT 2.13 类型变更 | 🟡 MEDIUM | 0.4.1 | bcrypt→4.0.1, PyJWT→2.7.0 |

---

## CI/CD 管道状态

| Workflow | 文件 | 触发条件 | 状态 |
|----------|------|---------|:----:|
| Lint | `.github/workflows/lint.yml` | push / PR | ✅ 通过 |
| Test | `.github/workflows/test.yml` | push / PR | ✅ 通过（后端 + 前端 + PostgreSQL service） |
| Release | `.github/workflows/release.yml` | tag 推送 | ✅ 可用 |

---

## 判定

### ✅ PASS — v0.5.0 满足 M6 可靠性门禁全部条件

- 72 后端测试 + 27 前端测试 + 5 E2E 场景全部通过
- 6 个缺陷已修复并验证
- 3 个 CI workflow 配置正确且可运行
- 回退路径明确（git tag v0.4.0）
- 无技术债务或临时方案残留
