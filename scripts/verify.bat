@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
:: verify.bat — DevPulse 全量验证脚本 (v0.0.9)
:: 从项目根目录或任意位置运行均可，自动定位项目路径

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

set PASS=0
set FAIL=0
set TOTAL=9

echo ========================================
echo   DevPulse 全量验证
echo ========================================
echo.

:: ============================================================
:: 1. Python 环境检查
:: ============================================================
echo [1/9] Python 环境检查 ...
python --version >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] Python 未安装
    set /a FAIL+=1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   %%i
    echo   [PASS]
    set /a PASS+=1
)
echo.

:: ============================================================
:: 2. Node.js 环境检查
:: ============================================================
echo [2/9] Node.js 环境检查 ...
node --version >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] Node.js 未安装
    set /a FAIL+=1
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo   %%i
    echo   [PASS]
    set /a PASS+=1
)
echo.

:: ============================================================
:: 3. Rust 环境检查（不阻塞，Tauri 打包才需要）
:: ============================================================
echo [3/9] Rust 环境检查 ...
rustc --version >nul 2>nul
if !errorlevel! neq 0 (
    echo   [WARN] Rust 未安装 (仅 Tauri 打包需要，不阻塞)
    set /a PASS+=1
) else (
    for /f "tokens=*" %%i in ('rustc --version 2^>^&1') do echo   %%i
    echo   [PASS]
    set /a PASS+=1
)
echo.

:: ============================================================
:: 4. 后端依赖安装
:: ============================================================
echo [4/9] 后端依赖安装 ...
cd backend
pip install -e ".[dev]" -q >nul 2>nul
python -c "import devpulse" >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] 后端依赖安装失败
    set /a FAIL+=1
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 5. 前端依赖安装
:: ============================================================
echo [5/9] 前端依赖安装 ...
cd desktop
call pnpm install --frozen-lockfile >nul 2>nul
if !errorlevel! neq 0 (
    echo   [WARN] pnpm install 失败，尝试 npm install ...
    call npm install >nul 2>nul
    if !errorlevel! neq 0 (
        echo   [FAIL] 前端依赖安装失败
        set /a FAIL+=1
    ) else (
        echo   [PASS] (via npm)
        set /a PASS+=1
    )
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 6. 后端测试
:: ============================================================
echo [6/9] 后端测试 (pytest) ...
cd backend
python -m pytest tests/ -q >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] 后端测试未通过
    set /a FAIL+=1
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 7. 后端 lint (ruff)
:: ============================================================
echo [7/9] 后端 lint (ruff) ...
cd backend
ruff check devpulse/ tests/ >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] ruff 检查未通过
    set /a FAIL+=1
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 8. 前端类型检查 (tsc --noEmit)
:: ============================================================
echo [8/9] 前端类型检查 (tsc --noEmit) ...
cd desktop
call npx tsc --noEmit >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] TypeScript 类型检查未通过
    set /a FAIL+=1
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 9. 前端构建
:: ============================================================
echo [9/9] 前端构建 (npm run build) ...
cd desktop
call npm run build >nul 2>nul
if !errorlevel! neq 0 (
    echo   [FAIL] 前端构建失败
    set /a FAIL+=1
) else (
    echo   [PASS]
    set /a PASS+=1
)
cd ..
echo.

:: ============================================================
:: 汇总输出
:: ============================================================
echo ========================================
echo   验证完成: !PASS!/%TOTAL% 通过
if !FAIL! gtr 0 (
    echo   失败项: !FAIL! 项需要修复
    echo ========================================
    endlocal
    exit /b 1
) else (
    echo   全部通过!
    echo ========================================
)

endlocal