# BUILD.md — DevPulse 构建与部署指南

> **本文档覆盖开发环境搭建、构建打包、CI/CD 配置和版本发布检查清单。**

---

## 开发环境搭建

### 系统要求

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10 - 3.11 | 后端服务 + 爬虫引擎 + MetaGPT 管线 |
| Node.js | 20 LTS+ | 前端 React + Tauri 桌面壳 |
| pnpm | 8.x+ | 前端包管理器（替代 npm，更快更省空间） |
| Rust | 1.75+ | Tauri 桌面壳编译 |
| PostgreSQL | 15+ | 服务端数据库 |
| Git | 2.40+ | 版本控制 |

### Windows 开发环境搭建步骤

```powershell
# 1. 安装 Rust（Tauri 依赖）
winget install Rustlang.Rustup
rustup default stable

# 2. 安装 Node.js 20 LTS
winget install OpenJS.NodeJS.LTS

# 3. 安装 pnpm
npm install -g pnpm

# 4. 安装 Python 3.11
winget install Python.Python.3.11

# 5. 验证环境
python --version   # 应输出 Python 3.11.x
node --version     # 应输出 v20.x.x
pnpm --version     # 应输出 8.x.x
rustc --version    # 应输出 1.75+
cargo --version    # 应输出 1.75+
```

---

## 项目初始化命令序列

```powershell
# 1. 克隆仓库
git clone https://github.com/your-org/DevPulse.git
cd "E:\Github Project\DevPulse"

# 2. Python 后端环境
cd api-server
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
deactivate
cd ..

# 3. React 前端 + Tauri
cd desktop
pnpm install
cd ..

# 4. 安装 MetaGPT
pip install metagpt

# 5. 安装质量检查工具
pip install ruff black pyright pytest
pnpm add -g eslint prettier typescript vitest

# 6. 验证全链路环境
python -c "import fastapi, metagpt, playwright; print('Python OK')"
cd desktop && pnpm run type-check && cd ..
cargo check --manifest-path desktop\src-tauri\Cargo.toml
```

---

## 开发模式运行

### dev.bat — 一键启动开发环境

> 文件位置：`E:\Github Project\DevPulse\scripts\dev.bat`

```batch
@echo off
chcp 65001 >nul
title DevPulse Development Environment
echo ======================================
echo   DevPulse Development Environment
echo ======================================
echo.

:: 启动后端 FastAPI（端口 8000）
echo [1/3] Starting Backend (FastAPI :8000)...
start "DevPulse-Backend" cmd /k "cd /d "E:\Github Project\DevPulse\api-server" && .\venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 等待后端就绪
timeout /t 3 /nobreak >nul

:: 启动前端 dev server（端口 5173）
echo [2/3] Starting Frontend (Vite :5173)...
start "DevPulse-Frontend" cmd /k "cd /d "E:\Github Project\DevPulse\desktop" && pnpm run dev"

:: 打开浏览器
echo [3/3] Opening Browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo ======================================
echo   DevPulse is running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ======================================
```

### 手动启动各组件

```powershell
# Terminal 1: 后端
cd "E:\Github Project\DevPulse\api-server"
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2: 前端
cd "E:\Github Project\DevPulse\desktop"
pnpm run dev

# Terminal 3: Tauri 开发模式
cd "E:\Github Project\DevPulse\desktop"
pnpm run tauri dev
```

---

## .exe 打包流程

### PyInstaller 方案：build_exe.bat

> 文件位置：`E:\Github Project\DevPulse\scripts\build_exe.bat`

```batch
@echo off
chcp 65001 >nul
title DevPulse Build — PyInstaller
echo ======================================
echo   DevPulse PyInstaller Build
echo ======================================
echo.

cd /d "E:\Github Project\DevPulse"

:: Step 1: 构建前端静态文件
echo [1/4] Building Frontend...
cd desktop
call pnpm run build
cd ..

:: Step 2: 安装 PyInstaller
echo [2/4] Installing PyInstaller...
pip install pyinstaller

:: Step 3: 打包
echo [3/4] Packaging with PyInstaller...
pyinstaller ^
  --onefile ^
  --console ^
  --name DevPulse ^
  --add-data "desktop\dist;desktop\dist" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.protocols ^
  --hidden-import uvicorn.lifespan ^
  --hidden-import fastapi ^
  --hidden-import sqlalchemy ^
  --hidden-import playwright ^
  --hidden-import metagpt ^
  --collect-all metagpt ^
  api-server\main.py

:: Step 4: 输出
echo.
echo [4/4] Build Complete!
echo Output: E:\Github Project\DevPulse\dist\DevPulse.exe
dir dist\DevPulse.exe
echo.
echo Run: .\dist\DevPulse.exe
```

| 维度 | 说明 |
|------|------|
| **输出路径** | `dist\DevPulse.exe` |
| **体积** | 约 50-80 MB（含 Python 运行时 + 依赖） |
| **启动方式** | 双击运行，自动启动 FastAPI 服务 + 打开浏览器 |
| **适用场景** | 后端独立分发、CI 构建产物 |

### Tauri 方案

```powershell
cd "E:\Github Project\DevPulse\desktop"
pnpm run tauri build
```

| 维度 | 说明 |
|------|------|
| **输出路径** | `desktop\src-tauri\target\release\DevPulse.exe` |
| **体积** | 约 8-15 MB（Rust 编译 + WebView2 复用） |
| **输出格式** | `.exe` + `.msi` 安装包 |
| **启动方式** | 原生桌面应用，系统托盘驻留 |
| **适用场景** | 正式桌面应用发布 |

---

## CI/CD Pipeline 配置

### GitHub Actions：lint + type-check

```yaml
# .github/workflows/ci.yml
name: CI — Lint & Type Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  python-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff pyright
      - run: ruff check api-server/ core/
      - run: pyright api-server/ core/

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: desktop/pnpm-lock.yaml
      - run: cd desktop && pnpm install
      - run: cd desktop && pnpm run lint
      - run: cd desktop && pnpm run type-check

  rust-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo fmt --check --manifest-path desktop/src-tauri/Cargo.toml
      - run: cargo clippy --manifest-path desktop/src-tauri/Cargo.toml -- -D warnings
```

### GitHub Actions：unit test

```yaml
# .github/workflows/test.yml
name: CI — Unit Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  python-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: devpulse_test
          POSTGRES_DB: devpulse_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r api-server/requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest api-server/ core/ --cov --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:devpulse_test@localhost:5432/devpulse_test

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: desktop/pnpm-lock.yaml
      - run: cd desktop && pnpm install
      - run: cd desktop && pnpm run test -- --coverage
```

### GitHub Actions：build + artifact upload

```yaml
# .github/workflows/build.yml
name: CI — Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build-tauri:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: desktop/pnpm-lock.yaml
      - uses: dtolnay/rust-toolchain@stable
      - run: cd desktop && pnpm install
      - run: cd desktop && pnpm run tauri build
      - uses: actions/upload-artifact@v4
        with:
          name: DevPulse-Windows
          path: |
            desktop/src-tauri/target/release/bundle/msi/*.msi
            desktop/src-tauri/target/release/bundle/nsis/*.exe
```

### GitHub Actions：release workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate Changelog
        id: changelog
        run: |
          git log $(git describe --tags --abbrev=0 HEAD^)..HEAD --pretty=format:"- %s" > CHANGELOG.md
          cat CHANGELOG.md

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: CHANGELOG.md
          files: |
            dist/DevPulse.exe
            desktop/src-tauri/target/release/bundle/msi/*.msi
          draft: false
          prerelease: ${{ contains(github.ref, 'alpha') || contains(github.ref, 'beta') }}
```

---

## 版本发布检查清单

### M6 Reliability Gate（每次发布前必须全通）

```
🔒 回归验证:
- [ ] 所有已有 API 端点功能正常
- [ ] 前端页面无白屏/报错
- [ ] 测试套件全绿（pytest + vitest）
- [ ] 回退路径明确（知道从哪个 commit/tag 回退）
- [ ] 边界用例覆盖（空 Trending / 单项目 / 大量项目）

🏥 迭代健康检查:
- [ ] 代码结构清晰，无临时方案残留
- [ ] 无 "以后再重构" 的 TODO/注释
- [ ] 依赖项在 requirements.txt / package.json 中正确声明
- [ ] 新引入模式与现有模式一致
- [ ] 无 dead code 或注释掉的代码
```

### M8 Quality Gate（版本发布五维扫描）

```
① 架构 audit:
- [ ] 无循环依赖
- [ ] 无 God class（>300 行单函数）
- [ ] 模块边界清晰

② 安全 audit:
- [ ] 无硬编码凭据/API Key
- [ ] 所有入口有输入校验
- [ ] 无 SQL/命令注入向量

③ 性能 audit:
- [ ] 无 N+1 查询
- [ ] 关键路径有缓存策略
- [ ] 无同步阻塞在异步路径中

④ 代码质量 audit:
- [ ] 圈复杂度 <15（所有函数）
- [ ] 无魔法数字
- [ ] 命名规范一致
- [ ] 无 >5 行的重复代码

⑤ 测试 audit:
- [ ] 关键路径覆盖率 ≥ 80%
- [ ] 无 flaky test
- [ ] 边界用例有覆盖
```

---

## 全量验证脚本：verify.bat

> 文件位置：`E:\Github Project\DevPulse\scripts\verify.bat`

```batch
@echo off
chcp 65001 >nul
title DevPulse Verification
echo ======================================
echo   DevPulse Full Verification
echo ======================================
echo.

cd /d "E:\Github Project\DevPulse"

:: === Python 后端 ===
echo ── Python Backend ──────────────────────
echo [1/6] ruff check...
ruff check api-server\ core\
if %errorlevel% neq 0 goto :fail

echo [2/6] pyright type-check...
pyright api-server\ core\
if %errorlevel% neq 0 goto :fail

echo [3/6] pytest unit tests...
pytest api-server\ core\ --cov --cov-report=term-missing
if %errorlevel% neq 0 goto :fail

:: === 前端 ===
echo ── Frontend ────────────────────────────
echo [4/6] eslint lint...
cd desktop
call pnpm run lint
if %errorlevel% neq 0 goto :fail

echo [5/6] tsc type-check...
call pnpm run type-check
if %errorlevel% neq 0 goto :fail

echo [6/6] vitest unit tests...
call pnpm run test -- --run
if %errorlevel% neq 0 goto :fail
cd ..

:: === 成功 ===
echo.
echo ======================================
echo   ALL CHECKS PASSED ✅
echo ======================================
exit /b 0

:fail
echo.
echo ======================================
echo   VERIFICATION FAILED ❌
echo   Check output above for details.
echo ======================================
exit /b 1
```

---

## 各阶段验证命令速查

| 阶段 | 命令 | 说明 |
|------|------|------|
| Python lint | `ruff check api-server\ core\` | 代码风格 + 逻辑检查 |
| Python type | `pyright api-server\ core\` | 类型标注验证 |
| Python test | `pytest api-server\ core\ --cov` | 单元测试 + 覆盖率 |
| Python format | `black api-server\ core\` | 自动格式化 |
| 前端 lint | `cd desktop && pnpm run lint` | ESLint 检查 |
| 前端 type | `cd desktop && pnpm run type-check` | TypeScript 类型检查 |
| 前端 test | `cd desktop && pnpm run test -- --run` | Vitest 单元测试 |
| Rust check | `cargo check --manifest-path desktop\src-tauri\Cargo.toml` | Rust 编译检查 |
| Rust lint | `cargo clippy --manifest-path desktop\src-tauri\Cargo.toml` | Clippy 检查 |
| 全量验证 | `scripts\verify.bat` | 一键运行全部检查 |

---

## 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) — 项目架构与 Phase 1 详细规划
- [GUARDRAILS.md](./GUARDRAILS.md) — 质量门禁标准
- [README.md](./READMe.md) — 项目介绍与快速开始