@echo off
chcp 65001 >nul
:: dev.bat — DevPulse 开发环境一键启动 (v0.0.9)
:: 从项目根目录或任意位置运行均可，自动定位项目路径
:: 默认 META_GPT_ENABLED=false，如需启用请手动修改为 true

set PROJECT_ROOT=%~dp0..
set META_GPT_ENABLED=false
cd /d "%PROJECT_ROOT%"

echo ========================================
echo   DevPulse 开发环境启动
echo ========================================
echo.
echo [配置] META_GPT_ENABLED = %META_GPT_ENABLED%
echo.

:: 1. 启动后端 FastAPI (端口 8000)
echo [1/3] 启动后端 (FastAPI :8000) ...
start "DevPulse Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && set META_GPT_ENABLED=%META_GPT_ENABLED% && uvicorn devpulse.main:app --reload --port 8000"

:: 2. 等待后端启动
timeout /t 3 /nobreak >nul

:: 3. 启动前端 Vite dev server (端口 1420)
echo [2/3] 启动前端 (Vite :1420) ...
start "DevPulse Frontend" cmd /k "cd /d "%PROJECT_ROOT%\desktop" && npm run dev"

:: 4. 等待前端启动
timeout /t 3 /nobreak >nul

:: 5. 打开浏览器
echo [3/3] 打开浏览器 ...
start "" "http://localhost:1420"

echo.
echo ========================================
echo   DevPulse 已启动:
echo     后端:     http://localhost:8000
echo     前端:     http://localhost:1420
echo     API 文档: http://localhost:8000/docs
echo ========================================
echo.
echo 关闭命令行窗口即可停止所有服务。
pause