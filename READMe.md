# DevPulse

<p align="center">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Android%20%7C%20HarmonyOS-9cf?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome">
</p>

<p align="center">
  <b>AI 开源趋势，尽在掌握</b><br>
  <sub>Tracking GitHub Trending AI/ML projects, delivered as beautiful weekly reports. ✨</sub>
</p>

---

## What is DevPulse?

DevPulse is a **cross-platform developer tool** that automatically tracks trending AI/ML open-source projects on GitHub and presents them in visually stunning weekly digests.

> 上线后中文名将更名为「**AI 潮汐**」—— 如潮汐般准时，为你推送 AI 开源世界的最新动态。

###  Why DevPulse?

- **⏰ 省时** — 不用每天刷 GitHub Trending，每周一份周报就够了
- **🎯 聚焦 AI/ML** — 只关心 AI 领域，不做大杂烩
- **🧠 智能解读** — LLM 为每个项目生成中文摘要，一眼看懂项目价值
- **📱 跨平台** — Windows 桌面端 + Android 移动端 + 鸿蒙，全端覆盖
- **🎨 精美 UI** — 卡片式设计，阅读体验堪比杂志

---

##  Features

| Feature | Description |
|---|---|
| 🔥 Trending 榜单 | 每周自动抓取 GitHub Trending AI/ML 项目 |
| 🤖 AI 摘要 | 多模型（Claude / GPT / DeepSeek / Qwen）生成中文解读 |
| ⭐ 收藏管理 | 收藏感兴趣的项目，随时回顾 |
| 🔔 推送通知 | 新周报发布时系统级通知提醒 |
| 📊 趋势图表 | 可视化展示项目 Star 增长、语言分布 |
| 🌐 离线支持 | 移动端缓存上周数据，无网络也能看 |
| 🖥️ 桌面驻留 | Tauri 系统托盘，后台定时更新 |

---

##  Architecture Overview

```
┌──────────────────────────────────────────────┐
│                 DevPulse                      │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ Windows │  │ Android  │  │  HarmonyOS   │ │
│  │ (Tauri) │  │(Capacitor)│  │(ArkUI+Web)  │ │
│  └────┬────┘  └────┬─────┘  └──────┬──────┘ │
│       └────────────┼───────────────┘         │
│                    │                          │
│            ┌───────┴───────┐                  │
│            │  React 18 SPA │  共享 UI 层      │
│            └───────┬───────┘                  │
│                    │                          │
│            ┌───────┴───────┐                  │
│            │  FastAPI 后端  │  数据服务层      │
│            └───────┬───────┘                  │
│                    │                          │
│         ┌──────────┼──────────┐               │
│    ┌────┴────┐ ┌───┴────┐ ┌──┴──────┐        │
│    │ Crawler │ │   LLM  │ │   DB    │        │
│    │(Playwright)│(Summary)│ │(PG+SQLite)│     │
│    └─────────┘ └────────┘ └─────────┘        │
│                                               │
│    ┌──────────────────────────────────┐       │
│    │  MetaGPT Multi-Agent Pipeline    │       │
│    │  Crawler→Analyzer→Summarizer→    │       │
│    │  Publisher (SOP Orchestration)   │       │
│    └──────────────────────────────────┘       │
└──────────────────────────────────────────────┘
```

---

##  Quick Start

### 一键启动（推荐）

```batch
:: Windows 下双击运行即可
scripts\dev.bat
```

启动后自动打开浏览器访问 `http://localhost:5173`。

### 手动启动

```bash
# Clone the repository
git clone https://github.com/your-org/DevPulse.git
cd DevPulse

# Install Python dependencies (Backend)
cd api-server
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000

# Install frontend dependencies (Desktop)
cd ../desktop
npm install

# Start Tauri dev server
npm run tauri dev
```

> Android / HarmonyOS build instructions → see [ARCHITECTURE.md](./ARCHITECTURE.md)
> 完整构建与打包指南 → see [BUILD.md](./BUILD.md)

---

##  Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **管线引擎** | **MetaGPT** (MIT) | 多 Agent SOP 编排，ICLR 2024 验证 |
| **质量门禁** | **ai-dev-guardrails v3.0** | 五层防御体系 + M1-M9 监控模块 |
| **Frontend UI** | React 18 + TypeScript | Cross-platform shared code, mature ecosystem |
| **Styling** | Tailwind CSS 3.x | Rapid development, responsive design |
| **State** | Zustand | Lightweight, no boilerplate |
| **Charts** | Recharts | Simple React charting library |
| **Desktop Shell** | Tauri 2.x (Rust) | <10MB bundle, 20x lighter than Electron |
| **Mobile Shell** | Capacitor.js 6.x | Package React SPA as Android APK |
| **HarmonyOS** | ArkUI + WebView | HarmonyOS NEXT compatible |
| **Backend** | Python FastAPI | Best AI/crawler ecosystem |
| **Crawler** | Playwright + httpx | Handle GitHub anti-bot measures |
| **LLM** | Multi-model adapter | Claude / GPT / DeepSeek / Qwen |
| **Database** | PostgreSQL + SQLite | Scalable server + lightweight local |
| **Scheduler** | APScheduler + Tauri schedule | Server & desktop dual timers |

---

##  Project Structure

```
DevPulse/
├── core/                  # Python: 数据抓取 + LLM 摘要 + MetaGPT Agent
│   ├── crawler/           # GitHub Trending 页面解析器
│   ├── summarizer/        # LLM 摘要生成
│   ├── agents/            # MetaGPT Agent 角色定义
│   ├── pipeline/          # MetaGPT SOP 流水线编排
│   └── scheduler/         # 定时任务 (APScheduler)
├── api-server/            # FastAPI 服务端
├── desktop/               # Tauri + React 桌面应用
├── mobile/                # Capacitor 移动端壳
├── harmony/               # 鸿蒙适配层
├── shared/                # 跨平台共享代码
├── scripts/               # 构建与验证脚本
│   ├── dev.bat            # 一键启动开发环境
│   ├── build_exe.bat      # PyInstaller 打包
│   └── verify.bat         # 全量验证脚本
├── docs/                  # 文档
├── README.md              # 本文档
├── ARCHITECTURE.md        # 架构总览 + Phase 1 详细规划
├── GUARDRAILS.md          # 质量门禁标准（ai-dev-guardrails）
├── BUILD.md               # 构建与部署指南 + CI/CD 配置
├── CLAUDE.md
├── CODEX.md
├── QWEN.md
└── LICENSE
```

---

##  Roadmap

| Phase | Version Range | Goal |
|---|---|---|
| **Phase 1: Core Engine** | 0.0.1 → 0.1.0 | 脚手架 + 爬虫 + LLM + MetaGPT 管线 + Tauri 桌面 MVP + 门禁全通 |
| **Phase 2: Mobile** | 0.1.1 → 0.2.0 | Android APK release |
| **Phase 3: HarmonyOS** | 0.2.1 → 0.3.0 | HarmonyOS adaptation |
| **Phase 4: Operations** | 0.3.1 → 1.0.0 | Scheduled updates, push notifications, user feedback, multi-topic |

---

##  Documentation

| Document | Description |
|----------|------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构总览、技术选型、模块划分、Phase 1 详细规划、开源/AISkills 集成方案 |
| [GUARDRAILS.md](./GUARDRAILS.md) | 五条铁律、L0-L5 决策流、M1-M9 监控模块、反幻觉速查表、CI/CD 门禁标准 |
| [BUILD.md](./BUILD.md) | 环境搭建、dev.bat/exe 打包/Tauri 构建、GitHub Actions CI/CD、verify.bat |

---

##  Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [ARCHITECTURE.md](./ARCHITECTURE.md) for the full project structure and conventions.
All PRs must pass the quality gates defined in [GUARDRAILS.md](./GUARDRAILS.md).

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>上线后中文名：「AI 潮汐」 — 潮汐有信，AI 有声 🌊</sub>
</p>