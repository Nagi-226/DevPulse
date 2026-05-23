@echo off
chcp 65001 >nul
echo ========================================
echo   AI 潮汐 DevPulse — 开发模式启动
echo ========================================
echo.
echo [1/3] 启动后端 (FastAPI :8000)...
start "DevPulse Backend" cmd /k "cd /d "E:\Github Project\DevPulse\backend" && python -m devpulse.main"
echo [2/3] 启动前端 (Vite :1420)...
start "DevPulse Frontend" cmd /k "cd /d "E:\Github Project\DevPulse\desktop" && pnpm dev"
timeout /t 4 /nobreak >nul
echo [3/3] 打开浏览器...
start http://localhost:1420
echo.
echo 开发环境已启动!
echo   后端: http://localhost:8000
echo   前端: http://localhost:1420
echo   API文档: http://localhost:8000/docs
echo.
echo 关闭窗口即可停止所有服务。
pause