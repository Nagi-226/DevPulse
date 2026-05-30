# Docker 部署验证报告 — v0.5.0

> **状态**: 配置文件审查已完成，手动执行步骤待操作人员执行
> **审查日期**: 2026-05-30
> **审查对象**: `docker-compose.prod.yml`

---

## 前置条件

| 条件 | 状态 | 备注 |
|------|:----:|------|
| Docker Engine ≥ 24.0 | ⬜ | 待确认 |
| Docker Compose ≥ 2.20 | ⬜ | 待确认 |
| `.env.production` 文件已配置 | ⬜ | 需包含 DB_PASSWORD, JWT_SECRET_KEY 等 |
| 后端 Dockerfile 存在 (`backend/Dockerfile`) | ✅ | 已确认 |
| 前端已构建 (`desktop/dist/`) | ⬜ | `cd desktop && pnpm build` 后可用 |
| Nginx 配置目录存在 (`nginx/conf.d/`) | ⬜ | 待确认 |

---

## docker-compose.prod.yml 审查结果

### 服务清单

| 服务 | 镜像 | 端口 | 状态 |
|------|------|------|:----:|
| nginx | nginx:1.25-alpine | 80, 443 | ✅ 配置完整 |
| app | backend/Dockerfile (build) | 8000 (expose) | ✅ 配置完整 |
| db | postgres:16-alpine | 5432 (expose) | ✅ 配置完整 |
| certbot | certbot/certbot:latest | — | ✅ 配置完整 |

### 服务详情审查

#### nginx 服务
- [x] 挂载 `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`
- [x] 挂载 `./nginx/conf.d:/etc/nginx/conf.d:ro`
- [x] 挂载 `./desktop/dist:/usr/share/nginx/html:ro`
- [x] 挂载 certbot 证书卷 (`certbot_certs`, `certbot_www`，均为只读)
- [x] 日志卷 `nginx_logs` 独立挂载
- [x] 依赖 `app` 服务健康检查通过后才启动
- [x] 重启策略: `unless-stopped`
- [x] 日志轮转: 10MB × 3 文件

#### app 服务
- [x] 构建上下文: `./backend`，Dockerfile 路径正确
- [x] 镜像标签支持 `${IMAGE_TAG:-latest}` 覆盖
- [x] 环境变量完整（数据库、JWT、Sentry、日志、调度器、LLM、CORS）
- [x] `JWT_SECRET_KEY` 和 `DB_PASSWORD` 使用 `:?err` 强制要求
- [x] 健康检查: `curl -f http://localhost:8000/health`，30s 间隔，3 次重试
- [x] 依赖 `db` 服务健康检查通过后才启动
- [x] 重启策略: `unless-stopped`
- [x] 日志轮转: 10MB × 3 文件

#### db 服务
- [x] PostgreSQL 16 Alpine（轻量镜像）
- [x] 环境变量: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- [x] 数据持久化: `pgdata` 卷挂载到 `/var/lib/postgresql/data`
- [x] 健康检查: `pg_isready`，10s 间隔，5 次重试
- [x] 端口仅内部暴露（`expose` 而非 `ports`），安全性好
- [x] 重启策略: `unless-stopped`
- [x] 日志轮转: 10MB × 3 文件

#### certbot 服务
- [x] 使用官方 `certbot/certbot:latest` 镜像
- [x] 挂载证书卷 (`certbot_certs`) 和 webroot 卷 (`certbot_www`)
- [x] 自动续期: 每 12 小时尝试 `certbot renew`
- [x] 使用 webroot 方式验证（`--webroot-path=/var/www/certbot`）
- [x] 重启策略: `unless-stopped`

### 网络与卷

| 资源 | 类型 | 状态 |
|------|------|:----:|
| `devpulse-net` | bridge 网络 | ✅ |
| `pgdata` | local 卷（PostgreSQL 数据） | ✅ |
| `certbot_certs` | local 卷（Let's Encrypt 证书） | ✅ |
| `certbot_www` | local 卷（ACME 挑战验证） | ✅ |
| `nginx_logs` | local 卷（Nginx 日志） | ✅ |

### 审查结论

**✅ 审查通过** — `docker-compose.prod.yml` 结构完整、配置合理，无端口冲突、无缺失环境变量（强制变量已标注 `:?err`），健康检查链正确（db → app → nginx），日志轮转已配置。

---

## 验证步骤

### 1. 构建镜像

```bash
# 从项目根目录执行
docker compose -f docker-compose.prod.yml build --no-cache
```

**预期结果**: app 镜像构建成功，标签为 `devpulse-api:latest`

| 检查项 | 预期 | 实际 |
|--------|------|------|
| 构建无错误 | ✅ | TBD |
| 镜像大小合理（< 500MB） | ✅ | TBD |

### 2. 启动服务

```bash
# 确保 .env.production 已配置
docker compose -f docker-compose.prod.yml up -d
```

**预期结果**: 4 个服务全部启动，无立即退出

| 检查项 | 预期 | 实际 |
|--------|------|------|
| db 容器 Running + Healthy | ✅ | TBD |
| app 容器 Running + Healthy | ✅ | TBD |
| nginx 容器 Running | ✅ | TBD |
| certbot 容器 Running | ✅ | TBD |

### 3. 健康检查

```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 检查 app 健康端点
curl -f http://localhost:8000/health

# 检查 nginx 代理
curl -f http://localhost/health
```

| 检查项 | 预期 | 实际 |
|--------|------|------|
| 所有容器状态为 Up | ✅ | TBD |
| `GET /health` 返回 200 | ✅ | TBD |
| Nginx 代理转发正常 | ✅ | TBD |

### 4. API 端点验证

```bash
# Trending 端点
curl -s http://localhost/api/v1/trending/weekly | python -m json.tool | head -20

# Auth 端点
curl -s -X POST http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

| 端点 | 预期状态码 | 实际 |
|------|:---------:|------|
| `GET /api/v1/trending/weekly` | 200 | TBD |
| `GET /api/v1/health` | 200 | TBD |
| `POST /api/v1/auth/register` | 200/201 | TBD |

### 5. 前端访问验证

```bash
# 验证静态文件可访问
curl -s -o /dev/null -w "%{http_code}" http://localhost/
```

| 检查项 | 预期 | 实际 |
|--------|:----:|------|
| `GET /` 返回 200 | ✅ | TBD |
| 浏览器访问显示 DevPulse 首页 | ✅ | TBD |
| React 路由正常工作 | ✅ | TBD |

---

## 验证结果（TBD — 待手动执行）

> 以下由操作人员在实际部署环境中填写。

| 步骤 | 执行人 | 日期 | 结果 | 备注 |
|------|--------|------|:----:|------|
| 1. 构建镜像 | | | ⬜ | |
| 2. 启动服务 | | | ⬜ | |
| 3. 健康检查 | | | ⬜ | |
| 4. API 端点验证 | | | ⬜ | |
| 5. 前端访问验证 | | | ⬜ | |

---

## 已知问题

| # | 问题 | 严重程度 | 状态 |
|---|------|:--------:|:----:|
| 1 | certbot entrypoint 使用 `/bin/sh` 配合 `$!`（busybox ash 兼容，但非 POSIX 标准） | 🟢 低 | 已知，不影响功能 |
| 2 | app DATABASE_URL 硬编码用户 `devpulse`；若覆盖 `DB_USER` 需同步修改 | 🟢 低 | 文档提醒 |
| 3 | 无 Redis 缓存层 — 高并发下数据库可能成为瓶颈（当前规模可接受） | 🟡 中 | Phase 5+ 考虑 |

---

## 总结

docker-compose.prod.yml 配置文件审查通过，4 个服务定义完整，健康检查链正确，环境变量覆盖全面。手动验证步骤已准备就绪，待操作人员在目标环境中执行。
