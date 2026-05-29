# ARCHITECTURE.md — DevPulse 架构总览

> **本文档为所有 AI Agent（Claude Code / Codex / Qwen Code）的通用参考。**
> 任何 Agent 在开始编码前，必须先阅读本文档理解整体架构与规范。

---

## 项目愿景

DevPulse 是一个跨平台（Windows 11 / Android / 鸿蒙）的 **GitHub Trending AI/ML 项目周报应用**，自动抓取、分析、解读 GitHub 上 AI 领域的热门开源项目，以精美的卡片式界面呈现给开发者。

上线后中文名：「**AI 潮汐**」

---

## 系统架构（分层设计）

```
┌─────────────────────────────────────────┐
│           表现层 (Presentation)          │
│  Windows (Tauri)  Android (Capacitor)    │
│  鸿蒙 (ArkUI+WebView)                    │
├─────────────────────────────────────────┤
│           业务逻辑层 (Business)           │
│  项目排行 | 趋势分析 | 收藏管理 | 推送通知 │
├─────────────────────────────────────────┤
│           数据层 (Data)                  │
│  API 网关 | 爬虫引擎 | 缓存层 | 本地DB    │
├─────────────────────────────────────────┤
│           基础设施 (Infrastructure)       │
│  GitHub Trending 解析 | LLM 摘要生成      │
│  定时任务调度 | 跨平台构建                │
└─────────────────────────────────────────┘
```

---

## MetaGPT 多 Agent 编排流水线（新增）

DevPulse 的周报生成采用 MetaGPT 的 `Role → Action → SOP` 多 Agent 编排模型，构建四阶段流水线：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Crawler     │───▶│  Analyzer    │───▶│  Summarizer  │───▶│  Publisher   │
│  Agent       │    │  Agent       │    │  Agent       │    │  Agent       │
│   (数据采集)  │    │   (清洗分类)  │    │   (LLM摘要)  │    │   (周报发布)  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │                   │
   Playwright          BeautifulSoup        Claude/GPT/       Markdown/API/
   + httpx            + pandas             DeepSeek/Qwen      Card JSON
```

| Agent 角色 | MetaGPT 角色映射 | 职责 | 输入 | 输出 |
|-----------|-----------------|------|------|------|
| Crawler Agent | Engineer | 抓取 GitHub Trending 页面 | 定时触发器 | 原始 HTML + API JSON |
| Analyzer Agent | Architect | 数据清洗、去重、分类、语言/Stars/Topics 统计 | Crawler 输出 | 结构化项目清单 |
| Summarizer Agent | PM + Writer | LLM 中文摘要生成 | Analyzer 输出 | 项目摘要 Markdown |
| Publisher Agent | Engineer | 生成周报卡片 JSON，写入数据库，推送通知 | Summarizer 输出 | API 可消费的周报数据 |

**消息总线**：Agent 间通过 MetaGPT 的 `Message` 对象传递数据，支持异步流水线（每个 Agent 独立运行，通过消息队列解耦）。

---

## 技术选型与理由

| 层 | 技术 | 理由 |
|---|---|---|
| **管线引擎** | **MetaGPT**（MIT License） | 多 Agent SOP 编排，学术界验证，ICLR 2024 |
| **质量门禁** | **ai-dev-guardrails v3.0** | 五层防御体系（L0-L5 + M1-M9），企业级 CI/CD 标准 |
| 前端 UI | React 18 + TypeScript | 三端共享代码，生态成熟 |
| 桌面壳 | Tauri 2.x (Rust) — 0.1.0 已集成 | 体积小（<10MB），比 Electron 轻量 20 倍 |
| 移动端 | Capacitor.js | 一套 React 代码打包 Android APK |
| 鸿蒙 | ArkUI + WebView | 鸿蒙 NEXT 兼容方案 |
| 后端服务 | Python FastAPI | AI/爬虫生态最好 |
| 数据抓取 | Playwright + httpx | 应对 GitHub 反爬 |
| LLM 摘要 | 多模型可切换 | Claude / GPT / DeepSeek / Qwen |
| 本地存储 | SQLite (前端) + PostgreSQL (服务端) | 轻量 + 可扩展 |
| 状态管理 | Zustand | 比 Redux 轻量 |
| 样式 | Tailwind CSS | 快速开发、响应式 |
| 图表 | Recharts | 轻量 React 图表库 |
| 定时任务 | APScheduler (后端) + Tauri schedule (桌面) | 双端覆盖 |

---

## 开源项目集成方案

| 项目 | License | 集成方式 | 集成阶段 | 风险等级 |
|------|---------|---------|---------|---------|
| **MetaGPT** | MIT | 作为周报生成流水线引擎，利用 Role/Action/SOP 编排爬虫→分析→摘要→发布四阶段 | Phase 1（0.0.8） | 🟡 中 — 需定制 Agent 角色，框架较重 |
| **agency-agents** | MIT | 提供 120+ Agent 角色定义模板，为 DevPulse 各 Agent 编写专业 identity/prompt/workflow | Phase 1（0.0.8 并行） | 🟢 低 — 纯 Markdown 文件，零依赖 |
| **ruflo** | MIT | 备选编排引擎：GOAP 目标规划器 + 自学习记忆，适用于未来多主题订阅+Agent 协商场景 | Phase 3+（备选） | 🟠 偏高 — 深度绑定 Claude Code 生态，需适配 |
| **react-bits** | MIT/Commons Clause | 110+ 动画 React 组件，直接用于卡片式 UI 的动效和文本动画 | Phase 1（0.0.6） | 🟢 低 — 纯 UI 组件，shadcn CLI 安装 |
| **hermes-agent** | MIT | Cron 调度 + 多平台网关设计参考，用于定时发布功能规划 | Phase 1（0.0.5 参考） | 🟢 低 — 仅设计参考 |
| **Archon** | MIT | YAML 定义流水线模式参考，可借鉴用于 DevPulse 的"爬取→分析→生成→发布"流程 | Phase 1（参考） | 🟢 低 — 仅设计参考 |

---

## AISkills 集成方案

### 核心门禁：ai-dev-guardrails v3.0

**五层防御体系映射为 DevPulse 质量工程标准：**

| 层级 | 模块 | DevPulse 映射 |
|------|------|-------------|
| L0 | Planning Audit（规划审计） | 需求评审前自动检测逻辑缺口 |
| L1 | Minor Ambiguity（轻微模糊） | PR 描述模糊时 AI 自动补全并标记假设 |
| L2 | Clear Gap（明显缺口） | 架构决策记录（ADR）缺失时阻止编码 |
| L3 | Technical Error（技术错误） | 代码审查中自动检测不可能的技术方案 |
| L4 | Red Line Violation（踩红线） | 能力边界表检测：拒绝不可实现需求 |
| L5 | Critical Deviation（严重偏离） | 每次 Sprint 评审时对比项目契约与当前状态 |
| M1 | Project Contract（项目契约） | 每个 Phase 启动前锁定范围、架构、排除项 |
| M2 | Scope Dashboard（累积范围仪表盘） | GitHub Project 看板追踪 feature creep |
| M3 | Milestone Gates（里程碑关卡） | 3 个强制检查点：架构定稿 / 核心完成 / 扩展入口 |
| M4 | Planning Audit（用户规划审计） | 用户描述远期规划时自动审计可行性 |
| M5 | Deviation Detection（偏离检测） | 每次 PR 合入前对比设计文档 |
| M6 | Reliability Gate（可靠性关卡） | 回归验证 + 迭代健康检查（每次发布前） |
| M7 | L5 Defense Core（小白防御内核） | 强制锁定协议 + 复杂度乘法原则 |
| M8 | Quality Gate（质量审计） | 五维审计（架构/安全/性能/质量/测试） |
| M9 | Scope Fidelity Gate（范围忠实度） | 反过度工程检测（15 条速查规则） |

### 规范引擎：superpowers

| Skill | 核心原则 | DevPulse 开发阶段 |
|------|---------|-----------------|
| test-driven-development | "无失败测试不写生产代码" | 0.0.3+ 全阶段 |
| verification-before-completion | "无新鲜验证证据不得声称完成" | 0.0.5+ CI/CD 门禁 |
| subagent-driven-development | 每任务独立子 Agent + 两阶段审查 | 0.0.8 MetaGPT 集成 |
| writing-plans | 零上下文假设的设计文档规范 | 0.0.1 起全阶段 |
| brainstorming | 强制设计先行，9 步流程 | 每个 Phase 前期 |
| systematic-debugging | "无根因调查不提修复" | 全阶段 |

### 知识同步：neat-freak

| 功能 | DevPulse 集成点 |
|------|---------------|
| 变更影响矩阵 | 代码变更后自动更新 ARCHITECTURE.md / CLAUDE.md / README.md |
| 三类知识分层 | Agent 记忆（短期）→ CLAUDE.md（中期）→ docs/（长期） |
| 会话后审查 | 每次开发会话结束后自动同步文档 |

### 代码审查增强

| Skill | DevPulse 使用场景 |
|------|-----------------|
| production-code-audit | 版本发布前全量代码库五维扫描 |
| vibe-code-auditor | AI 生成代码（LLM 摘要管线）专项审查 |
| protect-mcp-governance | MCP 工具调用安全管控（Cedar 策略引擎） |

---

## CI/CD 门禁标准

### Git 前置门禁

| 阶段 | 触发时机 | 检查项 | 工具 |
|------|---------|-------|------|
| pre-commit | 每次 `git commit` | lint + format + type-check | ruff / black / pyright / eslint / tsc |
| pre-push | 每次 `git push` | unit test + build check | pytest / vitest / cargo check |

### PR 门禁（对照 ai-dev-guardrails M8）

每位 Reviewer 必须逐项确认：

```
PR Review Checklist:
- [ ] 代码与已确认架构一致（M5 偏离检测通过）
- [ ] 无硬编码凭据/密钥（M8 安全检查）
- [ ] 关键路径有测试覆盖（M8 测试维度）
- [ ] 无 scope creep（M9 范围忠实度）
- [ ] 复杂度合理（单函数 <300 行，圈复杂度 <15）
- [ ] 五条铁律全部遵守
```

### 发布门禁

**M6 Reliability Gate（每次发布前必须通过）：**

```
🔒 回归验证:
- [ ] 所有已有入口点功能正常
- [ ] 无副作用扩散到无关模块
- [ ] 测试套件全绿
- [ ] 回退路径明确
- [ ] 边界用例覆盖（空状态/错误状态/极限输入）

🏥 迭代健康检查:
- [ ] 代码结构清晰，无临时方案残留
- [ ] 无 "以后再重构" 的技术债务
- [ ] 依赖项在 package.json/requirements.txt 中声明
- [ ] 新引入模式与现有模式一致
- [ ] 2 周后其他人能无痛接手
```

**M8 Quality Gate（版本发布五维审计）：**

| 维度 | 检查项 | 通过标准 |
|------|-------|---------|
| 架构 | 循环依赖 / 紧耦合 / God Class | 0 CRITICAL |
| 安全 | 硬编码凭据 / SQL 注入 / 未校验输入 | 0 CRITICAL + 0 HIGH |
| 性能 | N+1 查询 / 缺失缓存 / 同步阻塞 | 0 HIGH |
| 质量 | 圈复杂度 / 魔法数字 / 重复代码 | 0 HIGH |
| 测试 | 关键路径覆盖 / 边界用例 / 无 flaky test | 核心覆盖率 ≥ 80% |

### 反幻觉速查表（15 条）

嵌入 `CLAUDE.md` / `CODEX.md` / `QWEN.md`，作为 AI Agent 行为准则：

| # | Agent Impulse | Instead, Do This |
|---|--------------|------------------|
| 1 | "I'll just use [trendy tech] because it's popular" | Check project tech stack, match it |
| 2 | "This function probably exists in the API" | Search codebase first, only use verified APIs |
| 3 | "I'll build the whole thing and figure out details later" | Build one module at a time, validate after each |
| 4 | "The user said 'simple' so I'll keep it minimal" | "Simple" is subjective — ask what it means |
| 5 | "I'll add this abstraction for future flexibility" | YAGNI — build what's needed now |
| 6 | "This edge case is unlikely, I'll skip it" | Handle it — "unlikely" in dev = "Tuesday" in production |
| 7 | "I'll generate boilerplate and mark TODOs for later" | TODOs are landmines — implement or flag as out of scope |
| 8 | "This function name is bad, let me rename it" | Not your task — note it, don't change it |
| 9 | "I'll fix this nearby bug while I'm here" | One fix, one PR — don't scope-creep |
| 10 | "I'll add a try-catch just in case" | Will this exception actually occur? If no, don't add |
| 11 | "This should be extracted into a utility" | Used only once? Inline > abstract |
| 12 | "Let me refactor the existing code first" | Refactoring is not the task |
| 13 | "The user probably also needs this feature" | User didn't say it → don't build it |
| 14 | "Let me future-proof this with an abstraction layer" | You are predicting the future — stop |
| 15 | "Let me optimize this path — it's not performant" | Measure first. No measurement = don't optimize |

### 五条铁律（嵌入 Code Review 清单）

| 铁律 | DevPulse 落地 | Review 检查点 |
|------|-------------|-------------|
| 1. 不盲从 | 用户提不合理需求（如"复刻 GitHub"）→ 拦截并给替代方案 | 是否有技术错误被直接实现？ |
| 2. 不脑补 | 模糊需求先确认，不自行填充未说明的细节 | 是否有未标记的假设？ |
| 3. 实事求是 | 能力边界表维护，越界任务明确拒绝 | 是否有伪代码/TODO 残留？ |
| 4. 可落地 | 所有交付代码可编译、可运行、含错误处理 | 新代码是否能直接跑？ |
| 5. 确认再开工 | 非微任务先总结理解、标记假设、提议方案 | 重大变更是否有 ADR？ |

---

## 目录结构

```
DevPulse/
├── core/                  # Python: 数据抓取与 LLM 摘要
│   ├── crawler/           # GitHub Trending 页面解析器
│   │   ├── trending_parser.py
│   │   └── repo_detail.py
│   ├── summarizer/        # LLM 摘要生成
│   │   └── llm_summary.py
│   ├── agents/            # MetaGPT Agent 角色定义
│   │   ├── crawler_agent.py
│   │   ├── analyzer_agent.py
│   │   ├── summarizer_agent.py
│   │   └── publisher_agent.py
│   ├── pipeline/          # MetaGPT SOP 流水线编排
│   │   └── weekly_report_flow.py
│   └── scheduler/         # 定时任务 (APScheduler)
│       └── jobs.py
├── api-server/            # FastAPI 服务端
│   ├── main.py            # 应用入口
│   ├── routers/           # 路由模块
│   │   ├── trending.py
│   │   ├── projects.py
│   │   └── summary.py
│   ├── models/            # 数据库模型 (SQLAlchemy)
│   │   ├── project.py
│   │   └── weekly_report.py
│   ├── services/          # 业务服务
│   │   ├── trending_service.py
│   │   └── llm_service.py
│   └── requirements.txt
├── desktop/               # Tauri + React 桌面应用
│   ├── src-tauri/         # Rust 后端
│   │   ├── src/
│   │   │   └── main.rs
│   │   └── Cargo.toml
│   ├── src/               # React 前端
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   └── stores/
│   └── package.json
├── mobile/                # Capacitor 移动端壳
│   ├── capacitor.config.ts
│   ├── android/
│   └── package.json
├── harmony/               # 鸿蒙适配层
│   ├── entry/
│   └── webview/
├── shared/                # 跨平台共享代码
│   ├── components/        # 共享 UI 组件
│   ├── types/             # TypeScript 类型定义
│   │   ├── project.ts
│   │   └── api.ts
│   ├── utils/             # 工具函数
│   │   ├── api-client.ts
│   │   └── formatters.ts
│   └── constants/
├── scripts/               # 构建与验证脚本
│   ├── dev.bat            # 一键启动开发环境
│   ├── build_exe.bat      # PyInstaller 打包
│   ├── verify.bat         # 全量验证脚本 (cmd)
│   └── full_verify.ps1    # 全量验证脚本 (PowerShell 增强版)
├── docs/                  # 文档
├── README.md
├── ARCHITECTURE.md        # 本文档
├── GUARDRAILS.md          # 质量门禁标准
├── BUILD.md               # 构建与部署指南
├── CLAUDE.md
├── CODEX.md
├── QWEN.md
└── LICENSE
```

---

## 模块划分

### 1. core — 数据抓取与清洗
- GitHub Trending 页面解析（HTML → 结构化数据）
- 项目详情 API 查询（Star、语言、Topics、README）
- 数据标准化与去重

### 2. ai-summarizer — LLM 摘要生成
- 调用大模型对项目进行中文解读
- 输出：一句话概述、核心功能、适用场景
- 支持多模型后端切换（Claude / GPT / DeepSeek / Qwen）

### 3. api-server — RESTful API 服务
- 为所有客户端提供数据接口
- 内置 Redis / 内存缓存策略
- JWT 认证（可选）

### 4. desktop — Tauri 桌面应用
- React 前端 + Rust 后端
- 系统托盘驻留
- 定时通知推送

### 5. mobile — Capacitor 移动壳
- Android APK 打包
- 离线缓存支持
- 原生通知集成

### 6. harmony — 鸿蒙适配层
- ArkUI 容器 + WebView 加载
- 鸿蒙原生通知 API 适配

### 7. shared — 跨平台共享代码
- UI 组件库
- 数据模型定义
- 工具函数 / API 客户端

---

## 数据流

```
GitHub Trending 页面 → Playwright 抓取 → 数据清洗
    → GitHub API 补充详情（Star、语言、Topics）
    → LLM 生成中文解读
    → PostgreSQL 存储 → FastAPI 暴露接口
    → 客户端请求（带缓存） → React 渲染卡片列表
```

详细步骤：

1. **定时触发**：APScheduler 每周一 9:00 (UTC+8) 触发抓取任务
2. **页面抓取**：Playwright 无头浏览器加载 `github.com/trending?since=weekly`
3. **HTML 解析**：BeautifulSoup 提取项目名称、描述、Star 数、语言
4. **详情补充**：调用 GitHub REST API `/repos/:owner/:repo` 获取 Topics、详细 Star 趋势、README
5. **LLM 摘要**：将项目信息发送给 LLM，生成中文摘要
6. **数据存储**：结构化数据写入 PostgreSQL
7. **API 暴露**：FastAPI 提供 RESTful 接口，支持分页、筛选、搜索
8. **客户端消费**：React SPA 请求 API，渲染卡片列表；支持本地 SQLite 缓存

---

## Phase 1 详细规划（0.0.1 → 0.1.0）

| 版本 | 目标 | 技术栈 | 交付物 | 验证标准 |
|------|------|-------|--------|---------|
| **0.0.1** | 项目脚手架 | Python FastAPI + React + Tauri | 完整目录结构 + 依赖锁定（requirements.txt / package.json / Cargo.toml） | `pip install -r requirements.txt` + `npm install` + `cargo build` 全部通过 |
| **0.0.2** | GitHub 爬虫模块 | Playwright + httpx + BeautifulSoup | trending_parser.py + repo_detail.py + GitHub API 集成 | 能成功抓取 trending 页面并输出 25 个项目 JSON |
| **0.0.3** | LLM 摘要管线 | OpenAI / Claude / Ollama 适配器 | llm_summary.py + Prompt 模板 + 多模型切换 | 输入项目 JSON → 输出中文摘要 Markdown |
| **0.0.4** | 元数据存储 | PostgreSQL + SQLite + SQLAlchemy | 数据模型定义 + 建表脚本 + 基础 CRUD | `pytest` 数据模型测试通过 |
| **0.0.5** | CLI 工具 + 定时调度 | argparse + APScheduler | CLI 入口 + cron 配置 + 定时爬取任务 | `python cli.py fetch` 成功触发完整抓取→存储流程 |
| **0.0.6** | React 前端骨架 | React 18 + Tailwind CSS + Zustand + react-bits | 页面路由 + 卡片组件 + 列表视图 | `npm run dev` 看到 Trending 卡片列表 |
| **0.0.7** | API 层 + 前后端联通 | FastAPI RESTful + api-client.ts | 全量 API 端点 + 前端数据请求 + 响应渲染 | 前端列表数据来自真实 API |
| **0.0.8** | MetaGPT 管道集成 | MetaGPT Role/Action/SOP | 爬虫Agent → 分析Agent → 摘要Agent → 发布Agent | 一键触发完整周报生成流水线 |
| **0.0.9** | 桌面可执行测试文件 | Python + Node.js + Tauri CLI | dev.bat / build_exe.bat / verify.bat + .exe 产出 | 三种启动方式全部可用 |
| **0.1.0** | Tauri 桌面 MVP 发布 | Tauri 2.x + NSIS/MSI | 桌面安装包 + 后端自动拉起 + 日志诊断 | 桌面双击启动 → 后端 5s 就绪 → 真实 Trending 数据展示 |

---

## Phase 1 完成状态（截止 2026-05-27）

**Phase 1 (0.0.1 → 0.1.0) 核心链路已完成，桌面安装包可用。已知缺口见下方。**

| 版本 | 完成日期 | 状态 | 备注 |
|------|---------|:----:|------|
| 0.0.1 | — | ✅ | 项目脚手架，三端依赖锁定 |
| 0.0.2 | — | ✅ | GitHub Trending 爬虫（Playwright） |
| 0.0.3 | — | ✅ | LLM 摘要管线，4 厂商适配器 |
| 0.0.4 | — | ✅ | SQLite 存储 + SQLAlchemy CRUD |
| 0.0.5 | — | ✅ | CLI + APScheduler 定时调度 |
| 0.0.6 | — | ✅ | React 前端骨架（Tauri + Vite） |
| 0.0.7 | — | ✅ | FastAPI 9 端点 + 前端数据联通 |
| 0.0.8 | — | ✅ | MetaGPT 4 Agent 流水线定义 |
| 0.0.9 | — | ✅ | dev.bat / build_exe.bat / verify.bat |
| 0.1.0 | 2026-05-24 | ✅ | Tauri 2.x NSIS/MSI 安装包 |

### Phase 1 已知缺口

| 缺口 | 影响 | 计划修复 |
|------|------|---------|
| `total_stars` 全为 0（爬虫仅抓 `stars_since`） | Trending 卡片无 Star 数 | 0.1.2 |
| `summary/key_points/tags` 全为 null | LLM 摘要管线未运行 | 0.1.3 |
| 无系统托盘驻留 | 关闭窗口即退出 | 0.1.4 |
| 无搜索/收藏 API 和 UI | README Feature 缺失 | 0.1.5-0.1.6 |
| 无推送通知 | README Feature 缺失 | 0.1.10 |
| 无趋势图表（Recharts 已安装未用） | README Feature 缺失 | 0.1.8 |
| M6/M8 门禁未执行 | 无 QA 报告 | 0.1.10 |

---

## Phase 2 迭代路线图（0.1.1 → 0.2.0）

共 10 个小版本，每版聚焦一个模块，逐步补齐功能并完成 Android 适配。

### 迭代总览

```
0.1.0 (基线) ──→ 0.1.5 (桌面完善) ──→ 0.1.10 (门禁全通) ──→ 0.2.0 (Android 发布)
                     │                              │
                     ├── BugFix + 数据修复          ├── 离线缓存
                     ├── LLM 摘要激活              ├── 趋势图表
                     ├── 系统托盘驻留              ├── 推送通知
                     └── 搜索 + 收藏               └── M6/M8 门禁
```

### 详细迭代计划

| 版本 | 主题 | 目标 | 前端变更 | 后端变更 | 验收标准 |
|------|------|------|---------|---------|---------|
| **0.1.1** 🔧 | BugFix 扫尾 | 修复桌面应用已知缺陷 | api-client 重试逻辑增强 | 版本号同步 0.1.0；CORS 完整；后端子进程隐藏控制台 | 双击 NSIS 安装 → 无命令行窗口 → 5s 内展示真实数据 |
| **0.1.2** 📊 | 数据质量修复 | 补齐 `total_stars` 和 `forks` | 卡片组件显示完整 Stars/Forks | 爬虫新增 GitHub API 补全详情；`repo_detail` 抓取仓库页 | Trending 卡片展示 3 项指标：Stars Since / Total Stars / Forks |
| **0.1.3** 🤖 | LLM 摘要激活 | 触发 AI 摘要管线 | 详情页渲染 `summary/key_points/tags` | `/repos/crawl` 后链路自动调用 LLM；摘要存储写入 DB | 每个 Trending 项目展示中文摘要 + 3 个关键点 + 标签 |
| **0.1.4** 🖥️ | 桌面驻留 | 系统托盘 + 关闭到托盘 | 托盘菜单：显示/退出/立即刷新 | Tauri `tray` 插件配置；最小化到托盘逻辑 | 点 X 不退出 → 托盘图标驻留 → 右键菜单可用 |
| **0.1.5** 🔍 | 搜索功能 | 按名称/语言/标签搜索 | SearchBar 组件 + SearchResult 列表页 | `/repos/?q=xxx&language=xxx` 全文搜索端点 | 输入关键词 → 即时过滤 → 点击进入详情 |
| **0.1.6** ⭐ | 收藏管理 | 收藏项目 + 收藏列表 | 详情页收藏按钮 + CollectionPage | `POST/DELETE /repos/star` + `GET /collections` 端点 | 点击收藏 → 二次确认取消 → 收藏页面查看列表 |
| **0.1.7** 📱 | Capacitor 基础 | Android 桥接适配 | `mobile/` 目录初始化；`capacitor.config.ts` 联网配置 | API base URL 环境变量注入；CORS 移动端适配 | `npx cap sync android` 成功；Android Studio 构建预览 |
| **0.1.8** 📈 | 趋势图表 | Recharts 图表集成 | 项目详情页 Star 增长曲线；首页语言分布饼图 | `/repos/trends?period=30d` 趋势数据端点 | 详情页看到 30 天 Star 折线图；首页看到语言占比饼图 |
| **0.1.9** 📴 | 离线缓存 | SQLite 本地缓存 + 断网降级 | 离线 Banner 提示；缓存数据优先渲染 | 前端 IndexedDB / SQLite 缓存层；ETag 条件请求 | 断网后打开 App → 展示上次缓存数据 + "离线模式" 标签 |
| **0.1.10** 🔔 | 推送通知 + 门禁 | 系统通知 + M6/M8 QA | 通知偏好设置页面 | Windows Toast 通知；APScheduler 周报发布触发 | 新周报生成 → 桌面通知弹窗；M6/M8 门禁报告通过 |
| **0.2.0** 🚀 | Android MVP 发布 | Android APK 正式构建 | 移动端 UI 自适应；触控优化 | API 生产部署（可选）；APK 签名打包 | `npx cap open android` → Gradle 构建 → 真机运行 |

### 迭代依赖关系

```
0.1.1 (BugFix) ──────┬──→ 0.1.2 (数据修复) ──→ 0.1.3 (LLM摘要)
                      │
                      ├──→ 0.1.4 (系统托盘) ──→ 0.1.10 (推送通知)
                      │
                      ├──→ 0.1.5 (搜索) ──→ 0.1.6 (收藏)
                      │
                      ├──→ 0.1.7 (Capacitor基础)
                      │         │
                      ├──→ 0.1.8 (趋势图表)
                      │
                      └──→ 0.1.9 (离线缓存)
                                 │
0.1.10 (门禁全通) ←──────────────┘
        │
0.2.0 (Android 发布) ←─── 0.1.7 (Capacitor基础)
```

> **说明**：0.1.2-0.1.9 可并行开发（前后端分离、无强依赖），0.1.10 为质量门禁汇总关卡，0.2.0 依赖 0.1.7 的 Capacitor 基础和 0.1.10 的门禁通过。

---

## Phase 3 迭代路线图（0.2.1 → 0.3.0）

共 8 个小版本。Phase 3 的核心目标是**从桌面/Android MVP 演进为跨三端（Win+Android+鸿蒙）的完整产品**，同时补齐云端基础设施（后端部署、用户系统、多端同步）。

### 迭代总览

```
0.2.0 (基线) ──→ 0.2.3 (云端用户) ──→ 0.2.6 (鸿蒙入门) ──→ 0.3.0 (鸿蒙发布)
      │                │                    │
      ├── 真机验证      ├── 后端云部署       ├── 鸿蒙 WebView 容器
      ├── Android修复   ├── 用户+收藏同步    ├── 鸿蒙原生通知
      └── Play Store    └── 多源+多主题      └── AppGallery 上架
```

### 详细迭代计划

| 版本 | 主题 | 目标 | 关键变更 | 验收标准 |
|------|------|------|---------|---------|
| **0.2.1** 📱 | Android 真机验证 | 在真实 Android 设备上跑通 APK，修复移动端 Bug | Gradle 构建参数调优；移动端 UI 触控适配（最小触摸区域 48px）；`webDir` 路径修正；`capacitor://localhost` CORS 验证 | `npx cap open android` → USB 真机运行 → 首页数据正常加载 |
| **0.2.2** ☁️ | 后端云部署 | 将 FastAPI 后端部署到云，移动端不再依赖本地 PC | Dockerfile + docker-compose.yml；SQLite → PostgreSQL 迁移脚本；环境变量注入 API_BASE_URL；健康检查 + 自动重启 | `curl https://api.devpulse.app/health` 返回 200；Android 真机切 Wi-Fi 正常访问 |
| **0.2.3** 👤 | 用户系统 + 跨端同步 | 登录/注册 + 收藏跨设备同步 | `users` 表 + JWT 认证；`/auth/register`、`/auth/login` 端点；`favorites` 关联 `user_id`；Web 端 AuthPage（登录/注册表单）；Token 持久化（localStorage） | 两个设备登录同一账号 → 收藏自动同步 |
| **0.2.4** 🌐 | 多源扩展 | 支持更多编程语言 + 接入 GitLab/Gitee 数据源 | 爬虫 `language` 参数覆盖 Top 20 语言；`TrendingSource` 抽象基类 → `GitHubSource` / `GitLabSource` / `GiteeSource`；前端语言筛选器扩展；数据源切换 Tab | Trending 页可切换 GitHub/GitLab/Gitee；语言筛选 20+ 选项 |
| **0.2.5** 🔔 | 移动端推送 | Android 原生推送通知 | Firebase Cloud Messaging (FCM) 集成；Capacitor `@capacitor/push-notifications` 插件；后端周报生成 → FCM 广播；推送偏好云同步到 `users` 表 | 新周报生成 → Android 通知栏弹出 → 点击打开详情 |
| **0.2.6** 🏗️ | 鸿蒙入门 | HarmonyOS 开发环境搭建 + WebView 容器 | DevEco Studio 项目初始化；`harmony/` 目录结构（entry + webview）；ArkUI Web 组件加载 `dist/`；`module.json5` 权限声明；基础路由适配 | DevEco Studio 模拟器 → 首页展示 Trending 列表 |
| **0.2.7** 🎨 | 鸿蒙 UI 适配 | 鸿蒙原生风格 + 通知 + 离线 | 鸿蒙 `@ohos.notification` 推送；ArkUI 原生标题栏 + 返回手势；`safe-area` 刘海屏适配；鸿蒙本地存储 `@ohos.data.preferences` 替代 IndexedDB | 鸿蒙真机 UI 与系统风格一致；通知可点击跳转 |
| **0.2.8** 🧪 | 鸿蒙 QA + 商店准备 | 三端全量回归测试 + AppGallery 上架材料 | 全端回归测试矩阵（Win/Android/鸿蒙）；AppGallery 上架截图 + 描述文案；隐私政策页面；性能基线（首屏 <2s）；无障碍适配 | 三端测试通过率 >95%；AppGallery 审核材料齐全 |
| **0.3.0** 🚀 | 鸿蒙正式发布 | HarmonyOS AppGallery 上架 | HAP/HSP 签名打包；AppGallery Connect 上传；商店审核通过 | AppGallery 搜索结果可见 DevPulse「AI 潮汐」 |

### 迭代依赖关系

```
0.2.1 (Android真机) ──┬──→ 0.2.2 (云部署) ──→ 0.2.3 (用户系统)
                       │                          │
                       │                          ├──→ 0.2.4 (多源扩展)
                       │                          │
                       ├──→ 0.2.5 (移动推送) ←────┘ (依赖云+用户)
                       │
                       ├──→ 0.2.6 (鸿蒙入门)
                       │         │
                       │         └──→ 0.2.7 (鸿蒙UI) ──→ 0.2.8 (QA) ──→ 0.3.0 (发布)
                       │
                       └── 0.2.3/0.2.4/0.2.5 与 0.2.6/0.2.7 可并行推进
```

> **关键依赖**：0.2.2（云部署）是移动端可用性的前提——当前 Android 依赖本地 PC 后端，不部署到云就无法独立使用。0.2.6（鸿蒙）依赖 0.2.5 的 Capacitor 插件模式作为参考，但两者可并行。

### 技术选型新增

| 领域 | 技术 | 理由 |
|------|------|------|
| 云部署 | Docker + Render/Railway | 低成本免费额度、自动 SSL、Git 集成部署 |
| 数据库升级 | PostgreSQL (Supabase/Neon) | 免费 tier 500MB，支持 JWT Row-Level Security |
| 用户认证 | JWT (PyJWT) + bcrypt | 轻量、无状态、无需 OAuth 三方依赖 |
| 移动推送 | Firebase Cloud Messaging | Android 原生支持、Capacitor 插件成熟 |
| 鸿蒙框架 | ArkUI + Web 组件 | 鸿蒙 NEXT 官方推荐，WebView 复用现有前端 |
| 鸿蒙本地存储 | @ohos.data.preferences | 鸿蒙原生 KV 存储，替代 IndexedDB |

### 与 Phase 4（运营增强）的边界

Phase 3 的终点是**三端发布**，以下功能留给 Phase 4（0.3.1→0.4.0 → 指向 1.0.0）：
- 生产环境部署（VPS + HTTPS + 监控告警）
- 内容品控（自动审核 + 人工管理后台）
- 用户互动（评论、点赞、分享）
- AI 个性化推荐（基于收藏/浏览历史）
- 性能优化（SSR、CDN、Lighthouse ≥90）
- 多语言 i18n + SEO
- iOS 适配（可选，根据用户需求）

---

## Phase 4 迭代路线图（0.3.1 → 0.4.0）

共 8 个小版本。Phase 4 的核心目标是**从 MVP 演进为生产级产品**——真实部署、内容品控、用户增长、性能打磨，最终以 0.4.0 作为 v1.0.0 的候选发布版。

### 迭代总览

```
0.3.0 (基线) ──→ 0.3.3 (用户互动) ──→ 0.3.6 (管理后台) ──→ 0.4.0 (正式版)
      │                │                    │
      ├── 生产部署      ├── 评论/点赞/分享   ├── 数据看板
      ├── HTTPS+监控    ├── AI推荐引擎       ├── 用户管理
      └── 自动周报      └── 性能+CDN         └── i18n+SEO
```

### 详细迭代计划

| 版本 | 主题 | 目标 | 关键变更 | 验收标准 |
|------|------|------|---------|---------|
| **0.3.1** 🏭 | 生产部署 | VPS/云主机真实部署，域名+HTTPS，不再依赖开发环境 | Nginx + Let's Encrypt SSL；Docker Compose 生产配置；`devpulse.app` 域名绑定；日志轮转 + 错误报警（Sentry）；环境变量管理（`.env.production`）；`api-client.ts` 正式 API 地址 | `curl https://api.devpulse.app/health` 200；三端均可通过公网 API 使用 |
| **0.3.2** 📰 | 内容品控 | 周报自动生成 → 人工审核 → 定时发布 | LLM 摘要置信度评分（`confidence_score` 0-1）；低分项目标记 `review_required`；`/admin/pending-reviews` 审核端点；APScheduler 每周一 09:00 自动生成 + 10:00 自动发布已审核内容；Markdown → HTML 渲染优化 | 周报自动生成 → 审核页勾选 → 定时发布 → 前端展示 |
| **0.3.3** 💬 | 用户互动 | 评论、点赞、分享 | `Comment` 模型（user_id + repo_id + content）；`POST/DELETE /repos/{full_name}/comments`；`POST /repos/{full_name}/like` 点赞接口；详情页评论列表 + 输入框；分享按钮（复制链接 + 生成分享图）；`InteractionService` 互动统计 | 详情页底部查看评论→发表评论→点赞→分享 |
| **0.3.4** 🧠 | AI 推荐 | 基于用户行为的个性化 Trending 排序 | `UserBehavior` 模型（浏览/收藏/点赞历史）；协同过滤推荐引擎（Python `scikit-learn` cosine similarity）；`GET /repos/recommended` 推荐端点；首页"为你推荐"Tab；冷启动策略（新用户显示全局热门） | 浏览 3 个项目后 → "为你推荐"展示相关仓库 |
| **0.3.5** ⚡ | 性能优化 | Lighthouse PWA ≥90，首屏 <1.5s | React `lazy()` + `Suspense` 路由级代码分割；Vite `manualChunks` 拆分 vendor/ui/charts；图片懒加载 `loading="lazy"`；Nginx gzip/brotli 压缩；CDN（Cloudflare）；PWA `manifest.json` + Service Worker | Lighthouse Performance ≥90；LCP <1.5s；离线 PWA 可用 |
| **0.3.6** 📊 | 管理后台 | 数据看板 + 用户管理 + 内容审核 | `pages/AdminPage.tsx`（仅 admin 角色可见）；Dashboard 看板（DAU/周报阅读量/收藏数/LLM 成本）；用户列表 + 封禁/解禁；爬虫手动触发面板；`User` 模型新增 `role` 字段（user/admin） | Admin 登录 → 看板数据实时 → 可审核/管理用户 |
| **0.3.7** 🌍 | 多语言 + SEO | i18n 国际化 + 搜索引擎曝光 | `react-i18next` 集成；中/英/日 三语翻译文件；语言检测（浏览器 preference + 手动切换）；`<meta>` SEO 标签（title/description/og:image）；sitemap.xml 动态生成；Google Analytics 埋点 | 切换语言 → 全站文案实时更新；Google 可索引项目详情页 |
| **0.3.8** 🧪 | QA + 发布准备 | 全端回归 + v1.0.0-rc | 更新 `test-matrix.md`（三端 × 全功能）；M6/M8 门禁执行；`npm run test` + `pytest` 覆盖率 ≥80%；压力测试（wrk 1000 并发）；发布公告文案；CHANGELOG.md | 全端回归通过率 >95%；门禁全通；0.4.0 CHANGELOG 就绪 |
| **0.4.0** 🚀 | 正式版发布 | v1.0.0-rc 公开上线 | `__version__ = "0.4.0"`（内部版本号，对外宣发 v1.0）；Google Play 上架审核；AppGallery 正式上架；Product Hunt 发布；官方 Twitter/小红书 宣发 | 三商店可下载；官网可访问；Product Hunt 上线 |

### 迭代依赖关系

```
0.3.1 (生产部署) ──┬──→ 0.3.2 (内容品控) ──→ 0.3.6 (管理后台)
                    │
                    ├──→ 0.3.3 (用户互动) ──→ 0.3.4 (AI推荐)
                    │         │
                    ├──→ 0.3.5 (性能优化) ←─┘ (联合优化首屏)
                    │         │
                    └──→ 0.3.7 (i18n+SEO)
                              │
0.3.8 (QA) ←─────────────────┘  0.3.2-0.3.7 并行完成
    │
0.4.0 (正式发布)
```

> **关键路径**：0.3.1 是基础（必须先部署才能测性能/SEO），0.3.2-0.3.7 可并行推进，0.3.8 是汇总 QA 关卡，0.4.0 是发布里程碑。

### 技术选型新增

| 领域 | 技术 | 理由 |
|------|------|------|
| 部署 | Nginx + Let's Encrypt + Docker Compose | 免费、成熟、社区广泛使用 |
| 监控 | Sentry（错误追踪） + UptimeRobot（可用性） | 免费 tier 够用，SDK 成熟 |
| CDN | Cloudflare（免费计划） | 全球节点、DDoS 防护、自动 HTTPS |
| 推荐引擎 | Python scikit-learn cosine_similarity | 轻量、无需 GPU、数据量小够用 |
| PWA | Workbox + vite-plugin-pwa | 自动生成 Service Worker |
| i18n | react-i18next | React 生态最成熟方案 |
| 分析 | Google Analytics 4 | 免费、全平台 SDK |
| SSL | Let's Encrypt + certbot auto-renew | 免费、自动化 |

### 与 v1.0.0 的边界

0.4.0 作为 v1.0.0-rc，以下功能留给真正的 1.0.0：
- iOS 适配（需 Apple Developer 账号 + Mac 构建环境）
- 付费订阅（Stripe/Paddle 集成 + 会员系统）
- 开放 API（API Key 管理 + Rate Limit + 文档）
- Community 社区（论坛/Discord 集成）
- 企业版（私有部署、SSO、SLA）

---

## 桌面可执行测试方案

### 方案 1：开发期 .bat 启动脚本

```batch
@echo off
:: dev.bat — DevPulse 开发环境一键启动 (v0.0.9)
:: 自动定位项目根目录，无需硬编码路径

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

:: 启动后端 FastAPI（端口 8000）
start "DevPulse Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && uvicorn devpulse.main:app --reload --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端 Vite dev server（端口 1420）
start "DevPulse Frontend" cmd /k "cd /d "%PROJECT_ROOT%\desktop" && npm run dev"

:: 等待前端启动
timeout /t 3 /nobreak >nul

:: 打开浏览器
start "" "http://localhost:1420"

echo DevPulse 已启动: 后端 :8000 / 前端 :1420
```

| 维度 | 说明 |
|------|------|
| **适用场景** | 日常开发调试 |
| **依赖项** | Python + Node.js + npm/pnpm |
| **输出路径** | 无文件产出，直接运行服务 |
| **优点** | 热重载，改代码即刷新；零构建时间 |
| **缺点** | 需要开发环境，不适合分发 |

### 方案 2：PyInstaller .exe

```batch
@echo off
:: build_exe.bat — DevPulse 后端打包为 Windows .exe (v0.0.9)
:: 自动定位项目根目录，无需硬编码路径

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

:: 构建前端静态文件
cd desktop
call npm run build
cd ..

:: 安装 PyInstaller
pip install pyinstaller -q

:: 打包后端（FastAPI + 内嵌前端静态文件）
pyinstaller ^
  --onefile ^
  --name DevPulse ^
  --add-data "desktop/dist;desktop/dist" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.protocols ^
  backend/devpulse/main.py

echo Build complete: dist\DevPulse.exe
```

| 维度 | 说明 |
|------|------|
| **适用场景** | 后端独立分发、无 Node.js 环境的用户 |
| **依赖项** | Python + PyInstaller |
| **输出路径** | `dist\DevPulse.exe`（单文件 ~50MB） |
| **优点** | 单文件可执行，无需安装 Python |
| **缺点** | 仅后端，不含 Tauri 桌面壳；启动较慢 |

### 方案 3：Tauri .exe

```
npm run tauri build
```

| 维度 | 说明 |
|------|------|
| **适用场景** | 正式桌面应用发布 |
| **依赖项** | Node.js + Rust + Tauri CLI + Microsoft Visual C++ Build Tools |
| **输出路径** | `desktop\src-tauri\target\release\DevPulse.exe`（约 8MB） |
| **输出格式** | `.exe`（Windows）+ `.msi`（安装包） |
| **优点** | 原生桌面体验，系统托盘，自动更新，体积小 |
| **缺点** | 构建依赖链较长，需 Rust 工具链 |

---

## 开发阶段规划

| 阶段 | 版本范围 | 目标 | 交付物 |
|------|---------|------|--------|
| Phase 1: 核心引擎 | 0.0.1 → 0.1.0 | 脚手架 + 爬虫 + LLM + 桌面 MVP + 门禁全通 | Tauri 桌面安装包 + 测试报告 |
| Phase 2: 移动端 | 0.1.1 → 0.2.0 | Android APK 发布 | Capacitor 打包版本 |
| Phase 3: 鸿蒙 | 0.2.1 → 0.3.0 | 鸿蒙适配 | 鸿蒙应用包 |
| Phase 4: 运营增强 | 0.3.1 → 1.0.0 | 定时更新、推送通知、用户反馈、多主题订阅 | 完整产品 |

---

### 0.1.1 (BugFix) 变更摘要（2026-05-25~27）

- **后端启动修复**：`lib.rs` `start_backend()` 重写，添加 TCP 端口就绪检测（15s 超时）+ `CREATE_NO_WINDOW` 子进程无控制台窗口
- **CORS 扩展**：`config.py` 新增 `https://tauri.localhost` / `http://tauri.localhost` / `http://127.0.0.1:1420`
- **前端重试**：`api-client.ts` 5 次重试机制（1s 间隔），应对后端冷启动延迟
- **cmd fallback 修复**：移除双 `/c` 参数，正确拆分 `cmd.exe` 参数
- **版本同步**：`__version__` 0.0.4 → 0.1.0
- **NSIS 重建**：`npx tauri build` 完整打包，包含上述所有修复

---

## API 设计概要

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/trending/weekly` | 获取本周 Trending 列表 |
| GET | `/api/v1/trending/history?week=2026-W21` | 获取历史周报 |
| GET | `/api/v1/projects/:owner/:repo` | 获取单个项目详情（含 LLM 摘要） |
| POST | `/api/v1/projects/:owner/:repo/star` | 收藏项目 |
| DELETE | `/api/v1/projects/:owner/:repo/star` | 取消收藏 |
| GET | `/api/v1/summary/weekly` | 获取 AI 生成的周报总结 |
| GET | `/api/v1/collections` | 获取用户收藏列表 |
| GET | `/api/v1/search?q=xxx` | 搜索项目（按名称/描述/摘要） |

### 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156
  }
}
```

### 缓存策略

- 客户端：SQLite 本地缓存最近 4 周数据，带 ETag 条件请求
- 服务端：内存缓存热门接口（5 分钟 TTL），PostgreSQL 持久化存储

---

## 开发规范

### 通用规范
- **注释与文档**：统一使用中文
- **代码标识符**：统一使用英文（变量名、函数名、类名等）
- **Git 提交信息**：`类型: 说明` 格式（`feat:` / `fix:` / `docs:` / `refactor:` / `test:`）
- **质量门禁**：所有 PR 和发布必须通过 M6 可靠性关卡 + M8 五维质量审计

### Python 规范
- Python 3.10-3.11，完整类型标注
- 使用 `black` 格式化，`ruff` 检查
- 异步使用 `async/await`（FastAPI 原生支持）
- MetaGPT Agent 角色定义放在 `core/agents/` 目录

### TypeScript / React 规范
- TypeScript strict mode
- 函数式组件 + Hooks，禁止 class 组件
- 状态管理统一使用 Zustand
- API 调用统一经过 `shared/utils/api-client.ts`
- UI 动画组件优先使用 react-bits（shadcn CLI 安装）

### Rust / Tauri 规范
- 最小权限原则（`tauri.conf.json` 中按需声明权限）
- Rust 代码用 `cargo fmt` + `cargo clippy`