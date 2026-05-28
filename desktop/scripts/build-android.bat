@echo off
chcp 65001 >nul
echo ========================================
echo  DevPulse Android 构建脚本
echo ========================================

cd /d "%~dp0\.."

echo [1/3] 安装依赖...
call pnpm install --frozen-lockfile

echo.
echo [2/3] 构建前端 (移动端)...
call pnpm build

echo.
echo [3/3] 同步到 Capacitor Android...
call npx cap sync android

echo.
echo ========================================
echo  构建完成！
echo  使用 Android Studio 打开 android/ 目录编译 APK
echo ========================================
pause