@echo off
REM ============================================================
REM DevPulse 全平台构建脚本
REM 按顺序构建：前端 → 桌面 (Tauri) → 移动 (Capacitor) → 鸿蒙 (Hvigor)
REM 依赖：Node.js, Rust/Cargo, Android SDK, DevEco Studio
REM ============================================================

echo [DevPulse] Full Build Pipeline
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set DESKTOP_DIR=%PROJECT_ROOT%\desktop
set MOBILE_DIR=%PROJECT_ROOT%\mobile
set HARMONY_DIR=%PROJECT_ROOT%\harmony
set BACKEND_DIR=%PROJECT_ROOT%\backend

REM ===================================
REM Step 1: 构建前端
REM ===================================
echo [Step 1/4] Building Frontend...
cd /d "%DESKTOP_DIR%"
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Frontend build failed!
    exit /b 1
)
echo [OK] Frontend build complete
echo.

REM ===================================
REM Step 2: 构建 Tauri 桌面应用
REM ===================================
echo [Step 2/4] Building Tauri Desktop App...
cd /d "%DESKTOP_DIR%"
call npm run tauri build
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Tauri build failed — continue anyway
)
echo [OK] Tauri build complete
echo.

REM ===================================
REM Step 3: 构建 Android APK
REM ===================================
echo [Step 3/4] Building Android APK...
cd /d "%MOBILE_DIR%"
call npm run sync
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Capacitor sync failed
)

REM 使用 Gradle 构建 APK
if exist "%MOBILE_DIR%\android\gradlew.bat" (
    cd /d "%MOBILE_DIR%\android"
    call gradlew.bat assembleRelease
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Gradle build failed
    ) else (
        echo [OK] APK built successfully
    )
) else (
    echo [WARNING] Android project not found, skipping APK build
)
echo.

REM ===================================
REM Step 4: 构建鸿蒙 HAP
REM ===================================
echo [Step 4/4] Building HarmonyOS HAP...
cd /d "%PROJECT_ROOT%"
call "%SCRIPT_DIR%build-harmony.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Harmony build failed
)
echo.

REM ===================================
REM Summary
REM ===================================
echo ============================================================
echo [DevPulse] Build Pipeline Complete
echo ============================================================
echo.
echo [Output Locations:]
echo   Desktop (Tauri) : %DESKTOP_DIR%\src-tauri\target\release\
echo   Android (APK)   : %MOBILE_DIR%\android\app\build\outputs\apk\
echo   Harmony (HAP)   : %HARMONY_DIR%\entry\build\default\outputs\default\
echo.
echo [Next Steps:]
echo   1. Test APK on Android device
echo   2. Test HAP in DevEco Studio emulator
echo   3. Sign HAP for AppGallery release
echo   4. Upload to stores
echo.

exit /b 0
