# CODEX.md — DevPulse Project Guide for Codex

## Project Overview
**DevPulse** (codename, will launch as "AI 潮汐") is a cross-platform developer tool that automatically tracks GitHub Trending AI/ML repositories and generates weekly Chinese-language analysis reports.

## Codex Environment Setup
- Use the workspace at: `E:\Github Project\DevPulse`
- All tasks should reference `ARCHITECTURE.md` as the source of truth
- Codex should follow the same directory structure and naming conventions

## Key Conventions for Codex
- TypeScript strict mode enabled
- React functional components only
- Python 3.11+ with full type annotations
- API routes follow RESTful conventions
- Commit messages in Chinese (`feature:` / `fix:` / `docs:` format)

## Phase 1 Priority Tasks
1. Implement `core/crawler/trending_parser.py` — parse GitHub Trending weekly page
2. Implement `core/crawler/repo_detail.py` — fetch repo details via GitHub API
3. Implement `core/summarizer/llm_summary.py` — generate Chinese summaries using multiple LLM backends
4. Set up `api-server/` with FastAPI skeleton and first endpoint
5. Write unit tests for each module

## Codex-Specific Tips
- Use `/speckit.specify` to create detailed specs before coding
- Use Codex's multi-file editing to scaffold entire modules at once
- Leverage Codex's test generation for comprehensive coverage
- Codex is optimized for generating complete files from scratch — use it for initial module scaffolding
- When you need a working prototype quickly, ask Codex to generate the full implementation in one pass
- For iterative development, use Codex's edit mode to refine existing files

## Codex Strengths in This Project
- **Scaffolding**: Generate entire module structures (directory + files) in one go
- **Boilerplate**: FastAPI routers, React components, database models
- **Tests**: Generate unit tests alongside implementation code
- **API Integration**: GitHub REST API client with error handling and rate limiting