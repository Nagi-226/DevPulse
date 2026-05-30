# DevPulse v0.5.0 — Quality Hardening

> **发布日期**: 2026-05-30
> **版本类型**: 质量加固（无新功能）
> **前置版本**: v0.4.0

---

## Key Numbers

| 指标 | v0.4.0 → v0.5.0 |
|------|:---------------:|
| 后端集成测试 | 0 → **72** |
| 前端测试 | 4 → **27** |
| E2E 场景 | 0 → **5** |
| Bug 修复 | **6** |
| 路由 Bug 发现并修复 | **2** |
| CI workflow 状态 | **3/3 全绿** |
| M6 门禁 | ✅ 首次通过 |
| M8 五维审计 | ✅ 首次通过 |

---

## What This Means

v0.5.0 **不添加新功能**。它证明了 v0.4.0 交付的所有功能是真实可用的。

- 每个 API 端点都有自动化测试覆盖
- 每个关键 UI 组件都有单元/组件测试
- 每个核心用户路径都有 E2E 场景验证
- CI 管道在每次代码提交时自动运行全部测试
- 两个路由 Bug 在测试中被发现并修复

这是一次「质量投资」——为后续 Phase 的快速迭代打下可靠基础。

---

## Upgrade Notes

### 对于开发者

```bash
# 后端：安装测试依赖
pip install -e "backend/.[dev]"

# 前端：安装测试工具链
cd desktop && pnpm install

# 运行全部测试
pytest tests/ -v          # 后端 72 tests
cd desktop && pnpm test   # 前端 27 tests
cd e2e && npx playwright test  # E2E 5 scenarios
```

### 对于 Docker 部署

```bash
# 重建镜像（numpy 依赖已修复）
docker compose -f docker-compose.prod.yml build --no-cache
```

### 回退路径

```bash
git checkout v0.4.0  # 回退到上一个稳定版本
```

---

## 相关文档

| 文档 | 路径 |
|------|------|
| M6 可靠性门禁 | `docs/gate-m6-0.5.0.md` |
| M8 五维质量审计 | `docs/gate-m8-0.5.0.md` |
| Docker 部署验证 | `docs/docker-verify-0.5.0.md` |
| 性能测试报告 | `docs/perf-report-0.5.0.md` |
| 完整变更日志 | `CHANGELOG.md#050--2026-05-30` |
