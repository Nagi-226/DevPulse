@echo off
REM ============================================================
REM DevPulse 鸿蒙构建脚本
REM 用途：构建前端 dist/ → 复制到 harmony/ → 使用 hvigor 打包
REM 依赖：Node.js, DevEco Studio (hvigor), 前端已构建
REM ============================================================

echo [DevPulse] Harmony Build Script
echo ============================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set HARMONY_DIR=%PROJECT_ROOT%\harmony
set DESKTOP_DIST=%PROJECT_ROOT%\desktop\dist

echo.

REM Step 1: 检查前端构建产物
if not exist "%DESKTOP_DIST%\index.html" (
    echo [ERROR] Frontend dist/ not found at %DESKTOP_DIST%
    echo [INFO]  Run "cd desktop ^&^& npm run build" first
    exit /b 1
)
echo [OK] Frontend dist/ found

REM Step 2: 复制前端产物到鸿蒙 rawfile 目录
set RAWFILE_DIR=%HARMONY_DIR%\entry\src\main\resources\rawfile\dist
if exist "%RAWFILE_DIR%" (
    rmdir /s /q "%RAWFILE_DIR%"
)
mkdir "%RAWFILE_DIR%"

xcopy /e /y "%DESKTOP_DIST%\*" "%RAWFILE_DIR%\"
echo [OK] Copied dist/ to harmony rawfile

REM Step 3: 使用 hvigor 构建 HAP
echo.
echo [INFO] Building HAP with hvigor...
cd /d "%HARMONY_DIR%"

REM 如果 hvigorw 不可用，尝试使用 DevEco Studio 命令行工具
if exist "hvigorw.bat" (
    call hvigorw.bat assembleHap --mode module -p module=entry@default -p product=default
    if %ERRORLEVEL% EQU 0 (
        echo [OK] HAP build successful
    ) else (
        echo [ERROR] HAP build failed
        exit /b 1
    )
) else (
    echo [WARNING] hvigorw.bat not found
    echo [INFO]  Please open this project in DevEco Studio and build manually
    echo [INFO]  Build command: Build ^> Build HAP(s) / APP(s) ^> Build HAP(s)
)

echo.
echo [DevPulse] Harmony build complete
echo ============================================================
echo [INFO] Output: %HARMONY_DIR%\entry\build\default\outputs\default\
echo.

exit /b 0
