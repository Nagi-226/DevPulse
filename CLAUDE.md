# CLAUDE.md — DevPulse Project Guide for Claude Code

## Project Context
You are working on **DevPulse** (later to be renamed "AI 潮汐"), a cross-platform desktop + mobile application that tracks GitHub Trending AI/ML projects and presents them in a beautifully designed weekly report.

## Tech Stack
- Frontend: React 18 + TypeScript + Tailwind CSS + Zustand + Recharts
- Desktop Shell: Tauri 2.x (Rust backend)
- Mobile Shell: Capacitor.js
- Backend Service: Python FastAPI + PostgreSQL + Playwright
- Shared: TypeScript models, utilities, API client

## Current Project State
Phase 0 — Architecture planning complete. Ready to start Phase 1 (Core Engine).

## Directory Structure
```
DevPulse/
├── core/                  # Python: crawler + summarizer
│   ├── crawler/          # GitHub Trending parser
│   ├── summarizer/       # LLM summary generator
│   └── scheduler/        # APScheduler tasks
├── api-server/           # FastAPI service
│   ├── routers/
│   ├── models/
│   └── services/
├── desktop/              # Tauri + React
│   ├── src-tauri/       # Rust backend
│   ├── src/             # React frontend
│   └── package.json
├── mobile/               # Capacitor shell
├── shared/               # Shared TypeScript code
│   ├── components/
│   ├── types/
│   └── utils/
├── docs/                 # Documentation
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── CODEX.md
└── QWEN.md
```

## Development Rules
- Write all comments and documentation in Chinese
- Keep code identifiers in English
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use Zustand for state, never Redux
- All API calls go through shared/api-client.ts
- Backend Python uses type hints everywhere
- Follow Tauri security guidelines (no unnecessary permissions)

## First Steps for Claude Code
1. Read ARCHITECTURE.md for full project vision
2. Start with core/crawler/ — implement GitHub Trending page parser
3. Use httpx + BeautifulSoup for initial version, upgrade to Playwright if blocked
4. Write tests alongside implementation
5. Commit working code at each checkpoint

## Claude Code Workflow Tips
- Claude Code excels at reading and synthesizing large codebases: use it to understand existing architecture before coding
- Use Claude Code for complex refactoring tasks that span multiple files
- Leverage Claude Code's deep reasoning for architectural decisions and trade-off analysis
- For multi-step tasks, break them down and let Claude Code plan the implementation order
- Use `/clear` to reset context when switching between major tasks

## Skills Integration

本项目集成了以下 superpowers 技能（位于 `.claude/skills/`）：

| Skill | 触发条件 | 用途 |
|-------|---------|------|
| test-driven-development | 所有新功能和 Bug 修复 | TDD 开发规范 |
| verification-before-completion | 提交前、声称完成前 | 强制验证 |
| subagent-driven-development | 多 Agent 并行任务 | MetaGPT 流水线 |
| systematic-debugging | 任何 bug/测试失败 | 根因分析 |
| writing-plans | 新 Phase 启动前 | 实施计划编写 |

核心纪律:
- NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
- NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
- 所有代码变更先 pytest + ruff + tsc + build 验证
- 遇到 bug 先完成 Phase 1 根因调查再修复