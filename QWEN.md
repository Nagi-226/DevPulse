# QWEN.md — DevPulse 项目指南 for Qwen Code / 通义灵码

## 项目背景
DevPulse（上线后更名「AI 潮汐」）是一个跨平台（Win11 / Android / 鸿蒙）的 GitHub Trending AI 项目周报应用。核心功能：自动抓取 GitHub Trending 中 AI/ML 项目 → LLM 生成中文解读 → 精美卡片界面展示。

## Qwen Code 工作区
- 根目录：`E:\Github Project\DevPulse`
- 完整架构文档：[ARCHITECTURE.md](./ARCHITECTURE.md)
- 当前阶段：Phase 0 完成，准备进入 Phase 1（核心引擎开发）

## 技术栈速查

| 模块 | 技术 | 版本要求 |
|------|------|----------|
| 前端 | React + TypeScript | 18.x |
| 样式 | Tailwind CSS | 3.x |
| 桌面 | Tauri | 2.x |
| 移动端 | Capacitor | 6.x |
| 后端 | FastAPI | 0.110+ |
| 爬虫 | httpx + BeautifulSoup | 最新 |
| 数据库 | PostgreSQL + SQLite | 16+ |
| LLM | 多模型适配 | Claude/GPT/DeepSeek/Qwen |

## 开发规范
- 所有注释和文档使用中文
- 代码标识符使用英文
- Python 代码需完整类型标注
- React 组件使用函数式 + Hooks
- 提交信息格式：`类型: 说明`（如 `feat: 添加 Trending 页面解析器`）

## 给 Qwen Code 的首批任务

1. **搭建 core/crawler/** — 实现 GitHub Trending Weekly 页面解析
   - 目标文件：`core/crawler/trending_parser.py`
   - 技术方案：httpx + BeautifulSoup 解析 HTML，提取仓库名称、描述、Star、语言
   - 注意：GitHub Trending 无官方 API，需 HTML 解析；注意反爬策略，控制请求频率

2. **搭建 api-server/** — FastAPI 骨架
   - 目标文件：`api-server/main.py` + 路由注册
   - 实现首个端点 `GET /api/v1/trending/weekly`

3. **实现 shared/** — 共享类型定义
   - 目标文件：`shared/types/project.ts`、`shared/types/api.ts`
   - 定义 Project、WeeklyReport、ApiResponse 等核心类型

4. **实现 LLM 摘要模块** — 优先适配通义千问
   - 目标文件：`core/summarizer/llm_summary.py`
   - 优先适配阿里云百炼 Qwen 模型作为默认 LLM 后端
   - 预留多模型切换接口（Claude / GPT / DeepSeek）

## 注意事项
- GitHub Trending 页面无官方 API，需 HTML 解析
- 注意 GitHub 反爬策略，控制请求频率（建议每次请求间隔 2~3 秒）
- 优先适配通义千问 / 阿里云百炼平台作为默认 LLM 后端
- 国内网络环境需考虑 API 可达性（GitHub API 可能需要代理）
- FastAPI 开发时开启 `--reload` 模式方便调试

## Qwen Code 优势场景

Qwen Code / 通义灵码在以下场景表现突出：

- **中文技术文档生成**：生成中文注释、API 文档、开发日志
- **Python 后端开发**：FastAPI 路由、SQLAlchemy 模型、异步爬虫
- **通义千问 API 集成**：阿里云百炼 SDK 调用、Prompt 工程
- **国内生态适配**：代理配置、镜像源设置、国内部署方案
- **代码审查**：对中文注释和文档的审查更加准确

## 推荐工作流

1. 使用 Qwen Code 的「智能补全」快速编写模板代码
2. 使用「代码解释」理解已有模块（如 crawler 解析逻辑）
3. 使用「生成注释」为 Python 模块添加中文文档字符串
4. 使用「生成单元测试」为关键模块补充测试用例
5. 使用「代码优化」审查性能瓶颈（如爬虫并发策略）