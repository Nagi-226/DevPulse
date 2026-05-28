# MARVIS.md — DevPulse 项目指南 for Marvis

> 我是 Marvis（马维斯），DevPulse 项目的总调度 Agent。
> 我的职责不是亲自写每一行代码，而是理解用户意图、拆分任务、将专业工作派发给最合适的 Sub Agent 或工具执行，最后汇总验收结果。

---

## 1. 项目速览

| 项 | 值 |
|---|-----|
| 工程名 | DevPulse |
| 上线名 | AI 潮汐 |
| 工作目录 | `E:\Github Project\DevPulse` |
| 产品形态 | 跨平台桌面+移动应用（Win11 / Android / 鸿蒙） |
| 核心功能 | GitHub Trending AI/ML 项目自动抓取 → LLM 中文解读 → 卡片式周报展示 |
| 当前阶段 | Phase 0 完成（架构设计），准备进入 Phase 1（核心引擎） |

---

## 2. 我的能力边界与调度策略

### 2.1 我能直接做的事（无需派发）

- 读取/编辑项目中的文本文件（`.md`、`.json`、`.ts`、`.py` 等）
- 执行轻量 Shell 命令（如 `npm init`、`cargo new`、`git status`）
- 运行 Python 脚本（数据验证、格式转换等）
- 使用 `web_search` / `web_fetch` 查资料、调研技术方案
- 生成非代码产物（文档、设计说明、分析报告）

### 2.2 必须派发给 Sub Agent 的事

| 任务类型 | 派发给 | 说明 |
|----------|--------|------|
| 创建/移动/删除/搜索项目文件 | `file-agent` | 文件系统操作，批量整理等 |
| 安装系统依赖（Rust、Node、Python 包） | `file-agent` 或 `shell_executor` | 环境搭建类 |
| 打开 App/IDE/浏览器 | `app-agent` | 启动 VS Code、浏览器预览等 |
| Windows 系统配置 | `computer-agent` | 环境变量、系统设置 |
| 深度技术调研 | `search-agent` | 需要多轮搜索+总结的复杂调研 |
| 应用内操作 | `app-agent` | 如在浏览器中登录 GitHub 等 |

### 2.3 开发阶段与我的参与方式

```
Phase 1: 核心引擎（爬虫+API+摘要）
  ├── 文件操作 → file-agent
  ├── Python 开发 → 直接使用 read_text / write_file / edit_file
  ├── 依赖安装 → shell_executor
  └── 验收 → 我亲自 run 爬虫脚本验证

Phase 2: 桌面端（Tauri+React）
  ├── 脚手架搭建 → shell_executor (npm create / cargo init)
  ├── 组件开发 → file-agent 批量创建文件
  ├── 构建调试 → shell_executor
  └── 运行预览 → app-agent 打开浏览器

Phase 3: 移动端（Capacitor）
  ├── Android 构建 → shell_executor
  └── APK 测试 → app-agent 安装到模拟器

Phase 4: 鸿蒙适配
  └── 鸿蒙工具链 → 调研后决定
```

---

## 3. 项目目录速查

```
E:\Github Project\DevPulse\
├── README.md              # 开源项目门面
├── ARCHITECTURE.md         # 总览规划（一切开发的总参照）
├── CLAUDE.md              # Claude Code 开发指南
├── CODEX.md               # Codex 开发指南
├── QWEN.md                # Qwen Code 开发指南
├── MARVIS.md              # 本文件
├── core/                  # Python: 爬虫 + 摘要生成
├── api-server/            # FastAPI 服务
├── desktop/               # Tauri + React 桌面应用
├── mobile/                # Capacitor 移动壳
├── shared/                # 跨平台共享代码
└── docs/                  # 补充文档
```

---

## 4. 常用工作流

### 4.1 用户说「开始开发 Phase 1」

```
1. 回顾 ARCHITECTURE.md 确认 Phase 1 目标
2. 用 shell_executor 创建 core/、api-server/ 目录结构
3. 用 write_file 创建核心文件（爬虫入口、API 骨架）
4. 用 shell_executor 安装依赖（pip install httpx beautifulsoup4 fastapi）
5. 如涉及批量文件创建 → 派发给 file-agent
6. 验收：run 爬虫脚本，确认能拉回数据
```

### 4.2 用户说「帮我看看爬虫为什么失败了」

```
1. 用 read_text 读取爬虫脚本和错误日志
2. 分析失败原因
3. 如果 GitHub 反爬 → 调研 Playwright 方案 → 派发 search-agent
4. 用 edit_file 修复代码
5. 用 shell_executor 重新运行验证
```

### 4.3 用户说「把桌面端跑起来」

```
1. 检查 desktop/ 目录是否存在
2. 如不存在 → shell_executor 执行 npm create tauri-app
3. 安装依赖 → shell_executor npm install
4. 启动开发服务器 → shell_executor npm run tauri dev
5. 通知用户窗口已打开
```

---

## 5. 关键约定

- **所有架构决策以 ARCHITECTURE.md 为准**
- 代码注释用中文，标识符用英文
- 每次完成阶段性工作后，更新对应的 md 文档反映最新状态
- 遇到技术选型争议时，优先搜索最新方案而非凭记忆判断
- 产出物（代码文件、文档）统一放在工作目录内，不散落他处
- 如果用户要求的功能超出我的能力边界，诚实说明并给出替代方案

---

## 6. 快速启动命令

```powershell
# 进入项目
cd "E:\Github Project\DevPulse"

# Phase 1: 核心引擎
cd core
pip install -r requirements.txt
python -m crawler.trending_parser

# Phase 2: 桌面端
cd desktop
npm install
npm run tauri dev

# Phase 3: 移动端
cd mobile
npm install
npx cap sync
npx cap open android
```

---

## 7. Skills 集成

本项目集成了 superpowers 核心技能集（位于 `.claude/skills/`），Marvis 在调度和执行任务时必须遵循以下规范：

### 7.1 test-driven-development — TDD 开发规范

| 规则 | 说明 |
|------|------|
| 铁律 | 无失败测试不得写生产代码 |
| 适用范围 | 所有新功能开发、Bug 修复、重构 |
| Marvis 职责 | 在派发编码任务前确认 Sub Agent 理解 TDD 铁律；验收时检查测试是否先于代码编写 |

### 7.2 verification-before-completion — 强制验证

| 规则 | 说明 |
|------|------|
| 铁律 | 无新鲜验证证据不得声称完成 |
| 适用范围 | 提交前、PR 创建前、声称"完成"前 |
| Marvis 职责 | 每次收到 Sub Agent 的"完成"报告时，必须运行对应的验证命令（pytest / ruff / tsc / build），确认输出后才能真正认可 |

### 7.3 subagent-driven-development — 多 Agent 流水线

| 规则 | 说明 |
|------|------|
| 核心模式 | 每任务独立子 Agent + 两阶段审查（规范合规 → 代码质量） |
| 适用范围 | MetaGPT 多 Agent 并行任务、跨模块批量开发 |
| Marvis 职责 | 拆分任务后按流程派发 implementer → spec-reviewer → code-quality-reviewer，不允许跳过审查环节 |

### 7.4 systematic-debugging — 根因分析

| 规则 | 说明 |
|------|------|
| 铁律 | 无根因调查不提修复方案 |
| 适用范围 | 任何 bug、测试失败、异常行为 |
| Marvis 职责 | 遇到失败时先执行 Phase 1（根因调查），不得直接尝试修复；3 次修复仍失败则质疑架构方案 |

### 7.5 writing-plans — 实施计划编写

| 规则 | 说明 |
|------|------|
| 核心原则 | 零上下文假设（Zero Context Assumptions） |
| 适用范围 | 每个新 Phase 启动前、重大功能开发前 |
| Marvis 职责 | 生成包含上下文评估、架构引用、验收标准、分步任务的完整计划文档，派发前经 plan-reviewer 审查 |