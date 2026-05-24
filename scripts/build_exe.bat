@echo off
chcp 65001 >nul
:: build_exe.bat — DevPulse 后端打包为 Windows 单文件 .exe (v0.0.9)
:: 从项目根目录或任意位置运行均可，自动定位项目路径

setlocal
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo ========================================
echo   DevPulse 后端打包 (PyInstaller)
echo ========================================
echo.

:: 1. 检查 Python 环境
echo [1/4] 检查 Python 环境 ...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo   [FAIL] Python 未安装，请先安装 Python 3.10+
    goto :fail
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   %%i
echo   [PASS]
echo.

:: 2. 安装 PyInstaller（如未安装）
echo [2/4] 检查 PyInstaller ...
pip show pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo   正在安装 PyInstaller ...
    pip install pyinstaller -q
    if %errorlevel% neq 0 (
        echo   [FAIL] PyInstaller 安装失败
        goto :fail
    )
)
echo   [PASS]
echo.

:: 3. 构建前端静态文件
echo [3/4] 构建前端静态文件 (desktop/dist) ...
cd desktop
call npm run build
if %errorlevel% neq 0 (
    echo   [FAIL] 前端构建失败
    cd ..
    goto :fail
)
cd ..
echo   [PASS]
echo.

:: 4. PyInstaller 打包
echo [4/4] PyInstaller 打包 ...
pyinstaller ^
  --onefile ^
  --name DevPulse ^
  --add-data "desktop/dist;desktop/dist" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.protocols ^
  backend/devpulse/main.py

if %errorlevel% neq 0 (
    echo   [FAIL] PyInstaller 打包失败
    goto :fail
)

echo.
echo ========================================
echo   构建完成!
echo   输出: dist\DevPulse.exe
if exist "dist\DevPulse.exe" (
    for %%A in ("dist\DevPulse.exe") do echo   文件大小: %%~zA 字节
)
echo ========================================
goto :eof

:fail
echo.
echo ========================================
echo   构建失败，请检查以上错误信息。
echo ========================================
endlocal
exit /b 1