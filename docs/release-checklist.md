# DevPulse 0.3.0 发布检查清单

> **版本**：0.3.0  
> **目标发布日期**：TBD  
> **检查清单版本**：v1.0

---

## Pre-Release Checklist

### 🔧 代码与构建

- [ ] 所有版本号统一为 `0.3.0`（`backend/__init__.py` / `desktop/package.json` / `tauri.conf.json` / `harmony/app.json5`）
- [ ] `backend/devpulse/config.py` 中 `CRAWLER_USER_AGENT` 更新为 `DevPulse/0.3.0`
- [ ] Docker 镜像构建成功：`docker build -t devpulse:0.3.0 .`
- [ ] `docker-compose up` → `curl localhost:8000/health` 返回 200
- [ ] 前端构建成功：`cd desktop && npm run build` → `dist/` 产生
- [ ] TypeScript 类型检查通过：`cd desktop && npx tsc --noEmit`
- [ ] Tauri 桌面构建成功（Windows .msi）
- [ ] Android APK 构建成功
- [ ] 鸿蒙 HAP 构建成功

### 🧪 测试

- [ ] 三端回归测试矩阵 ≥95% 通过率
- [ ] P0 用例 100% 通过
- [ ] 用户注册/登录流程完整可用
- [ ] 跨设备收藏同步验证通过
- [ ] FCM 推送端到端可用（海外网络）
- [ ] 鸿蒙 WebView 加载 + SPA 路由正常

### 📋 文档与合规

- [ ] 隐私政策已发布到 `https://api.devpulse.app/privacy`
- [ ] AppGallery 上架文案已准备
- [ ] 应用截图已准备（≥3 张，≥1280×800）
- [ ] 发布说明 (`docs/release_notes_0.3.0.md`) 已撰写
- [ ] 无 AppGallery 合规问题

### 🔒 安全

- [ ] JWT_SECRET_KEY 已更换为生产密钥（非默认值）
- [ ] HTTPS 已启用（Render/Railway 自动 SSL）
- [ ] CORS 白名单仅包含合法域名
- [ ] Firebase 凭证文件未提交到 Git
- [ ] `.env` 文件未提交到 Git

### 🚀 部署

- [ ] 后端已部署到 Render/Railway
- [ ] `curl https://api.devpulse.app/health` 返回 200
- [ ] Supabase/Neon PostgreSQL 连接正常
- [ ] Alembic 迁移已执行
- [ ] SQLite 历史数据已迁移到 PostgreSQL

### 🏪 商店提交

- [ ] 鸿蒙 HAP 已签名
- [ ] AppGallery Connect 上传成功
- [ ] 审核状态可查询

---

## Post-Release Checklist

- [ ] 各端版本更新通知已发送
- [ ] GitHub Release 已创建（含 Release Notes）
- [ ] 监控面板确认 API 无异常
- [ ] 用户反馈渠道正常（邮箱/GitHub Issues）

---

## 签字确认

| 角色 | 姓名 | 签字 | 日期 |
|------|------|:---:|------|
| 产品经理 | Alice | ⬜ | |
| 架构师 | Bob | ⬜ | |
| 工程师 | Alex | ⬜ | |
| QA | TBD | ⬜ | |

---

> 此清单需在发布前逐项确认。未完成项需注明原因和预计完成时间。
