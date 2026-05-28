@echo off
chcp 65001 >nul
:: build-android.bat — DevPulse Android APK 构建脚本
:: 从项目根目录或任意位置运行均可，自动定位项目路径

setlocal
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo ========================================
echo   DevPulse Android 构建
echo ========================================
echo.

:: ── [1/3] 构建前端 ──────────────────────────────────
echo [1/3] 构建前端 (desktop/dist) ...
cd desktop
call pnpm build
if %errorlevel% neq 0 (
    echo   [FAIL] 前端构建失败
    cd ..
    goto :fail
)
cd ..
echo   [PASS] 前端构建成功
echo.

:: ── [2/3] 同步 Capacitor ─────────────────────────────
echo [2/3] 同步 Capacitor Android ...
cd mobile

:: 安装依赖（如果未安装）
if not exist "node_modules" (
    echo   首次运行，安装 mobile 依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo   [FAIL] npm install 失败
        cd ..
        goto :fail
    )
)

:: 同步前端产物到 Android 项目
call npx cap sync android
if %errorlevel% neq 0 (
    echo   [FAIL] Capacitor sync 失败
    cd ..
    goto :fail
)
cd ..
echo   [PASS] Capacitor sync 成功
echo.

:: ── [3/3] 打开 Android Studio ────────────────────────
echo [3/3] 打开 Android Studio ...
cd mobile
call npx cap open android
cd ..

echo.
echo ========================================
echo   Android 构建完成！
echo   请在 Android Studio 中:
echo   1. 选择 Build ^> Build Bundle(s) / APK(s) ^> Build APK(s)
echo   2. APK 输出: mobile/android/app/build/outputs/apk/debug/
echo ========================================
goto :eof

:fail
echo.
echo ========================================
echo   Android 构建失败，请检查以上错误信息。
echo ========================================
endlocal
exit /b 1
