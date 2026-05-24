@echo off
chcp 65001 >nul
:: test_meta_gpt.bat — MetaGPT 集成一键测试 (v0.0.8)
:: 设置 META_GPT_ENABLED=true，启动后端并触发 MetaGPT 流水线

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo ========================================
echo   MetaGPT 集成测试 (v0.0.8)
echo ========================================
echo.

:: 设置 MetaGPT 开关
set META_GPT_ENABLED=true
echo [环境] META_GPT_ENABLED = %META_GPT_ENABLED%
echo.

:: 检查 metagpt 包
echo [1/4] 检查 MetaGPT 包安装状态...
python -c "import devpulse.agents.base; print('  devpulse.agents.base 导入成功')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   ❌ devpulse.agents 模块导入失败
    goto :error
)
echo   ✅ Agent 模块导入成功
echo.

:: 验证 Agent 实例化
echo [2/4] 验证 Agent 实例化...
cd /d "%PROJECT_ROOT%\backend"
python -c "from devpulse.pipeline.meta_gpt_coordinator import MetaGPTCoordinator; c = MetaGPTCoordinator(); print('  ✅ MetaGPTCoordinator 已就绪')" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   ❌ MetaGPTCoordinator 初始化失败
    goto :error
)
echo.

:: 启动后端 FastAPI
echo [3/4] 启动后端 (FastAPI :8000) ...
start "DevPulse MetaGPT Test" cmd /k "cd /d "%PROJECT_ROOT%\backend" && set META_GPT_ENABLED=true && uvicorn devpulse.main:app --reload --port 8000"
timeout /t 4 /nobreak >nul

:: 执行 MetaGPT 流水线
echo [4/4] 触发 MetaGPT 流水线 (python cli.py fetch) ...
cd /d "%PROJECT_ROOT%\backend"
python -m devpulse.cli.main fetch 2>&1 | findstr /I "MetaGPT"
if %ERRORLEVEL% NEQ 0 (
    echo   ⚠ 未检测到 MetaGPT 输出 — 请检查日志
) else (
    echo   ✅ MetaGPT 流水线输出已检测到
)
echo.

echo ========================================
echo   MetaGPT 集成测试完成
echo   检查上方输出确认流水线已触发
echo ========================================
echo.
echo 提示: 关闭命令行窗口可停止后端服务
pause
exit /b 0

:error
echo.
echo ========================================
echo   MetaGPT 集成测试失败
echo   请检查上方错误信息
echo ========================================
pause
exit /b 1