@echo off
chcp 65001 >nul
echo ========================================
echo  DevPulse 多端构建脚本 v0.1.0
echo ========================================
echo.
echo 选择目标平台:
echo   [1] Windows 桌面 (Tauri MSI + NSIS)
echo   [2] Android (Capacitor APK)
echo   [3] 全部平台
echo   [0] 退出
echo.
set /p choice="请输入选项 (0-3): "

cd /d "%~dp0\.."

if "%choice%"=="1" goto :windows
if "%choice%"=="2" goto :android
if "%choice%"=="3" goto :all
if "%choice%"=="0" goto :exit
echo 无效选项，请重试
goto :eof

:windows
echo.
echo ========================================
echo  构建 Windows 桌面端 (Tauri)
echo ========================================
call pnpm install --frozen-lockfile
call pnpm tauri build
echo.
echo Windows 安装包位于:
echo   src-tauri\target\release\bundle\msi\*.msi
echo   src-tauri\target\release\bundle\nsis\*.exe
goto :done

:android
echo.
echo ========================================
echo  构建 Android 端 (Capacitor)
echo ========================================
echo.
echo [提示] 请确认 .env.production 中的 VITE_API_BASE 已配置为后端实际 IP
echo.
call pnpm install --frozen-lockfile
call pnpm build
call npx cap sync android
echo.
echo Android 项目已准备好: android\
echo 用 Android Studio 打开 android\ 目录编译 APK
echo 或命令行: cd android ^&^& .\gradlew assembleDebug
goto :done

:all
call :windows
echo.
call :android
goto :done

:done
echo.
echo ========================================
echo  构建完成！
echo ========================================
pause
goto :eof

:exit
echo 已取消