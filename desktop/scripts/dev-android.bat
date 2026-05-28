@echo off
chcp 65001 >nul
echo ========================================
echo  DevPulse Android 开发模式 (热重载)
echo ========================================
echo.
echo 前提条件:
echo   1. 手机与 PC 在同一局域网
echo   2. 后端已启动: cd ..\..\backend ^&^& .\venv\Scripts\python -m devpulse
echo   3. 修改 capacitor.config.ts 中的 server.url 为本机 IP
echo.

cd /d "%~dp0\.."

echo [1/2] 启动 Vite 开发服务器...
start "DevPulse Vite" cmd /c "pnpm dev"

echo [2/2] 等待 Vite 就绪后启动 Android...
timeout /t 5 /nobreak >nul
npx cap run android

pause