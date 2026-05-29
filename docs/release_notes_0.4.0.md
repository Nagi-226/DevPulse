# 🚀 DevPulse 0.4.0 — Production Ready (v1.0.0-rc)

**发布日期**: 2026-06-01

---

## ✨ What's New

DevPulse 0.4.0 是从 MVP 到生产级产品的里程碑版本。我们完成了三大核心升级：

### 🌐 生产部署
DevPulse 现在可以真正部署到 VPS 上，通过域名和 HTTPS 向全球用户提供服务。Nginx 反向代理 + Let's Encrypt SSL + Cloudflare CDN 确保安全、快速的访问体验。

### 💬 用户互动
评论、点赞、分享——用户现在可以围绕开源项目进行交流。详情页新增了完整的评论区、一键点赞和分享功能。

### 🧠 AI 推荐
基于协同过滤的推荐引擎，根据你的浏览和收藏行为，为你发现相关的开源项目。新用户会自动看到全局热门榜单作为冷启动。

### ⚡ 性能优化
PWA 支持、路由级代码分割、图片懒加载、Brotli 压缩——Lighthouse Performance 得分 90+，首屏加载 <1.5s。

### 📊 管理后台
管理员可以查看 DAU、阅读量、LLM 成本等运营数据，管理用户（封禁/解禁/角色变更），以及审核 AI 生成的摘要内容。

### 🌍 国际化
支持中文、英文、日文三语界面，浏览器语言自动检测，动态 sitemap.xml 生成，SEO 元标签优化。

---

## 📦 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 反向代理 | Nginx | 1.25+ |
| SSL | Let's Encrypt + certbot | latest |
| 后端 | FastAPI (Python 3.11) | 0.115+ |
| 数据库 | PostgreSQL | 16 |
| 前端 | React 18 + TypeScript | - |
| PWA | Workbox | 7.x |
| i18n | react-i18next | 14.x |
| 推荐引擎 | scikit-learn | 1.5+ |
| 错误追踪 | Sentry | SDK 2.x/8.x |
| 分析 | GA4 (gtag) | latest |

---

## 🚦 部署指南

```bash
# 1. 配置环境变量
cp backend/.env.production.example backend/.env.production
# 编辑 .env.production，填入真实值

# 2. 构建并启动
docker compose -f docker-compose.prod.yml up -d

# 3. 初始化 SSL 证书（首次）
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d devpulse.app -d api.devpulse.app

# 4. 重启 Nginx 以加载 SSL
docker compose -f docker-compose.prod.yml restart nginx
```

---

## 🔗 商店上架

- **Google Play**: [devpulse.app/play](https://devpulse.app/play)
- **AppGallery**: [devpulse.app/huawei](https://devpulse.app/huawei)
- **Product Hunt**: [producthunt.com/posts/devpulse](https://www.producthunt.com/posts/devpulse)

---

## ⚠️ Breaking Changes

- 数据库 schema 变更：新增 `comments`, `likes`, `user_behaviors`, `daily_stats` 表
- `users` 表新增 `role`, `is_active` 字段
- `repositories` 表新增 `confidence_score`, `review_status`, `review_required` 字段
- 环境变量新增：`SENTRY_DSN`, `LLM_MONTHLY_BUDGET`, `CDN_BASE_URL`, `REVIEW_REQUIRED_THRESHOLD`
- Docker 启动方式变更：推荐使用 `docker-compose.prod.yml`

---

## 🙏 致谢

感谢所有 Alpha 测试用户的反馈！DevPulse 从个人项目成长为生产级产品，离不开社区的支持。
