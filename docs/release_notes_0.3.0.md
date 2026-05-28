# DevPulse 0.3.0 发布说明

> **发布日期**：2026-06-01  
> **代号**："Harmony Tide"  
> **版本范围**：0.2.1 → 0.3.0

---

## 🎉 重大更新

### 🌸 鸿蒙生态正式接入
- 新增 `harmony/` 目录，基于 ArkUI Web 组件加载前端 SPA
- 支持鸿蒙原生通知（@ohos.notification）
- 支持 @ohos.data.preferences 本地存储（替代 IndexedDB）
- 刘海屏/挖孔屏 safe-area 适配
- 侧滑返回手势支持
- 准备 AppGallery 上架

### ☁️ 后端云部署
- Docker 多阶段构建（Python 3.11-slim，约 200MB）
- docker-compose 编排（app + PostgreSQL 双服务）
- 支持 Render.com / Railway 一键部署
- SQLite → PostgreSQL 数据迁移工具
- Alembic 数据库迁移管理

### 👤 用户认证系统
- 邮箱 + 密码注册/登录（PyJWT + bcrypt）
- JWT access token（24h）+ refresh token（7d）
- 自动 Token 刷新（401 → silent refresh）
- localStorage Token 持久化 + 页面刷新自动恢复

### 🔄 跨设备收藏同步
- 收藏数据关联用户 ID（替代硬编码 "default"）
- 设备 A 收藏 → 设备 B 登录同账号 → 收藏列表一致
- 收藏/取消收藏端点 JWT 认证保护

### 🔀 多数据源扩展
- `TrendingSource` 抽象基类（策略模式）
- GitHub / GitLab / Gitee 三大数据源
- 前端 Tab 切换（🐙 GitHub / 🦊 GitLab / 🏮 Gitee）
- 20+ 编程语言筛选（含搜索功能）

### 🔔 移动推送（FCM）
- Firebase Cloud Messaging 集成
- 周报生成后自动推送通知
- Capacitor @capacitor/push-notifications 插件
- 推送偏好云同步（周报推送 / 重要项目推送）

### 📱 移动端体验优化
- 最小触摸区域 ≥48px（WCAG 2.1 AA）
- 下拉刷新 + 上拉加载更多
- 离线缓存自动降级（Dexie IndexedDB）
- Gradle 构建参数调优

---

## 📊 版本路线回顾

```
0.2.1 ████████░░░░░░░░░░░░░░ Android 真机验证
0.2.2 ░░░░░░░░████████░░░░░░ 后端云部署
0.2.3 ░░░░░░░░░░░░░░████████ 用户系统 + 跨端同步
0.2.4 ░░░░░░░░░░░░░░████████ 多源扩展
0.2.5 ░░░░░░░░░░░░░░░░░░████ 移动推送
0.2.6 ░░░░░░░░░░░░░░████████ 鸿蒙入门
0.2.7 ░░░░░░░░░░░░░░░░░░████ 鸿蒙 UI 适配
0.2.8 ░░░░░░░░░░░░░░░░░░░░██ QA + 商店准备
0.3.0 ░░░░░░░░░░░░░░░░░░░░░█ 鸿蒙正式发布 ◀ 当前位置
```

---

## 📦 文件变更统计

| 类型 | 数量 |
|------|:---:|
| 🆕 新建文件 | ~55 |
| ✏️ 修改文件 | ~18 |
| 📋 文档文件 | ~7 |
| **总计** | **~80** |

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 🖥️ 桌面壳 | Tauri 2.x | - |
| 📱 移动壳 | Capacitor 6.x | Android |
| 🌸 鸿蒙壳 | ArkUI Web 组件 | API 12+ |
| ⚛️ 前端 | React 18 + Vite 6 + Tailwind CSS | SPA |
| 🐍 后端 | FastAPI + SQLAlchemy 2.0 | Python 3.11 |
| 🗄️ 数据库 | PostgreSQL 16（生产）/ SQLite（开发） | - |
| 🔐 认证 | PyJWT + bcrypt (passlib) | HS256 |
| 📡 推送 | Firebase Cloud Messaging | - |
| 🐳 部署 | Docker + docker-compose | Render/Railway |

---

## ⚠️ 破坏性变更

1. **Favorite.user_id 类型变更**：从 `String(100)` → `Integer + ForeignKey(users.id)`
   - 影响：旧版"default"用户收藏数据需通过迁移脚本升级
   - 迁移方案：`migrations/versions/001_initial_schema.py`

2. **收藏端点需 JWT 认证**：`/repos/collections`、`/repos/{full_name}/star` 现在要求 Bearer Token
   - 影响：未登录用户无法收藏（需先注册/登录）

3. **后端 API 无 `/api/v1` 前缀**：仅 Vite dev 代理使用前缀
   - 影响：移动端/鸿蒙需设置 `VITE_API_BASE` 环境变量

---

## 🔜 下一步（0.3.1+）

- [ ] AppGallery 审核优化（如需要）
- [ ] HMS Push Kit 适配（国内华为设备）
- [ ] CDN 静态资源加速
- [ ] 多语言国际化（英文 UI）
- [ ] 性能优化（首屏 FCP < 1s）

---

## 🙏 致谢

感谢所有参与 DevPulse Phase 3 开发的贡献者！

---

> DevPulse — AI 潮汐，让开发者不错过每一个优秀开源项目 🌊
