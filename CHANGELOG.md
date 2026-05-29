# DevPulse Changelog

All notable changes to DevPulse will be documented in this file.

---

## [0.4.0] — 2026-06-01 (v1.0.0-rc)

### Added
- **Production Deployment (0.3.1)**:
  - Nginx reverse proxy with brotli/gzip compression
  - Let's Encrypt SSL via certbot with auto-renewal
  - Docker Compose production configuration (nginx + app + postgres + certbot)
  - Production environment variable template
  - Sentry error tracking for both backend and frontend
  - Cloudflare CDN integration guide
- **Content Quality (0.3.2)**:
  - LLM summary confidence scoring (0.0-1.0)
  - Multi-dimensional quality evaluation (keyword coverage, summary length, sentence completeness, language consistency)
  - `review_required` flag for low-confidence summaries
  - Admin review workflow: approve/reject pending reviews
  - Auto-approve mechanism for high-confidence summaries (≥ threshold)
  - `DailyStats` model for operational metrics tracking
- **User Interactions (0.3.3)**:
  - Comment system: create/delete/list comments on repos
  - Like system: toggle like/unlike per repo
  - Share functionality: copy link + Twitter share
  - Interaction statistics per repository
- **AI Recommendations (0.3.4)**:
  - Three-tier recommendation engine:
    - L1: Collaborative filtering (cosine similarity, ≥ 3 user behaviors)
    - L2: Content-based filtering (language/topic matching)
    - L3: Global trending (fallback for cold start)
  - "For You" tab on Trending page
  - `UserBehavior` model for recommendation training
- **Performance + PWA (0.3.5)**:
  - Route-level code splitting via `React.lazy()` + `Suspense`
  - Vite `manualChunks` for vendor/ui/charts split
  - PWA manifest + offline fallback page
  - Image lazy loading component
  - Skeleton loading states
  - Nginx static asset caching headers
- **Admin Dashboard (0.3.6)**:
  - Dashboard with DAU / page views / favorites / LLM cost cards
  - 30-day trend line chart (Recharts)
  - User management list with ban/unban + role management
  - Content review panel (approve/reject)
  - Manual crawl trigger
  - Role-based access control (`get_admin_user` dependency)
- **i18n + SEO (0.3.7)**:
  - react-i18next with Chinese (zh), English (en), Japanese (ja)
  - 7 translation namespaces: common, trending, detail, auth, settings, search, admin
  - Browser language auto-detection
  - Language switcher in Settings page
  - Dynamic sitemap.xml generation
  - Open Graph meta tags
  - GA4 analytics integration

### Changed
- **Models**: User now has `role` and `is_active` fields; Repository has `confidence_score`, `review_status`, `review_required`
- **Config**: Added `SENTRY_DSN`, `ENVIRONMENT`, `DEPLOY_MODE`, `LLM_MONTHLY_BUDGET`, `CDN_BASE_URL`, `REVIEW_REQUIRED_THRESHOLD`
- **Summarizer**: Now computes confidence score for each summary
- **Scheduler**: Added auto-review workflow after weekly report generation
- **DeepSeek Provider**: Added token-based cost tracking
- **Dependencies**: Added sentry-sdk, scikit-learn, Pillow, react-i18next, i18next, vite-plugin-pwa, @sentry/react

### Fixed
- Dockerfile now supports configurable `UVICORN_WORKERS` via environment variable
- Repository DAO `update_summary` now writes confidence_score and review_status
- Nginx config handles Let's Encrypt ACME challenge correctly

---

## [0.3.0] — 2026-05-28

### Added
- Three-platform release: Windows NSIS + Android APK + HarmonyOS AppGallery
- JWT authentication (register/login/refresh/me)
- User favorites with cloud sync
- Push notification preferences
- FCM push notification integration
- Star history tracking (30-day trend)
- Language distribution statistics
- Offline cache (Dexie IndexedDB)
- Collections page (my favorites)
- Settings page (notifications + cache)
- Enhanced health check endpoint

### Changed
- Database: SQLite → PostgreSQL 16 for production
- API: All auth-required endpoints now use JWT Bearer tokens
- Docker: Multi-stage build reducing image size to ~200MB
- CORS: Expanded origins for multi-platform support

---

## [0.2.0] — 2026-05-14

### Added
- Multi-source support: GitHub, GitLab, Gitee
- Language filter (20+ programming languages)
- Time range filter (daily/weekly/monthly)
- LLM-powered repository summaries (DeepSeek)
- Weekly report generation with overview
- HTML weekly report view
- APScheduler for automated weekly crawling
- Mobile responsive design
- Touch interaction optimization

---

## [0.1.0] — 2026-04-30

### Added
- Initial MVP release
- GitHub Trending data crawling (Playwright)
- Repository detail page
- Basic trending list with star/fork stats
- Tauri desktop application wrapper
- FastAPI backend with SQLite storage
