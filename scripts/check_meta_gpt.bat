@echo off
chcp 65001 >nul
:: check_meta_gpt.bat — MetaGPT 集成就绪检查 (v0.0.8)
:: 一键检查 MetaGPT 集成是否就绪

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"
set PASS=0
set FAIL=0

echo ========================================
echo   MetaGPT 集成就绪检查 (v0.0.8)
echo ========================================
echo.

:: 1. 检查 metagpt 包
echo [1] 检查 MetaGPT 包安装...
python -c "import devpulse.agents.base; print('    base.py 可用')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo     ✅ 通过
    set /a PASS+=1
) else (
    echo     ❌ 失败 — devpulse.agents.base 导入失败
    set /a FAIL+=1
)

:: 2. 检查四个 Agent 文件
echo [2] 检查 Agent 文件...

for %%F in (
    "agents\crawler_agent.py"
    "agents\analyzer_agent.py"
    "agents\summarizer_agent.py"
    "agents\publisher_agent.py"
) do (
    if exist "%PROJECT_ROOT%\backend\devpulse\%%F" (
        echo     ✅ %%F
        set /a PASS+=1
    ) else (
        echo     ❌ %%F — 文件不存在
        set /a FAIL+=1
    )
)

:: 3. 检查 config.py 中 META_GPT_ENABLED
echo [3] 检查 config.py META_GPT_ENABLED...
findstr /C:"META_GPT_ENABLED" "%PROJECT_ROOT%\backend\devpulse\config.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     ✅ config.py 包含 META_GPT_ENABLED
    set /a PASS+=1
) else (
    echo     ❌ config.py 缺少 META_GPT_ENABLED
    set /a FAIL+=1
)

:: 4. 检查 pipeline.py 开关逻辑
echo [4] 检查 pipeline.py 开关逻辑...
findstr /C:"META_GPT_ENABLED" "%PROJECT_ROOT%\backend\devpulse\services\pipeline.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     ✅ pipeline.py 包含 META_GPT_ENABLED 开关
    set /a PASS+=1
) else (
    echo     ❌ pipeline.py 缺少 META_GPT_ENABLED 开关
    set /a FAIL+=1
)

:: 5. 检查 coordinator
echo [5] 检查 MetaGPT Coordinator...
if exist "%PROJECT_ROOT%\backend\devpulse\pipeline\meta_gpt_coordinator.py" (
    echo     ✅ meta_gpt_coordinator.py
    set /a PASS+=1
) else (
    echo     ❌ meta_gpt_coordinator.py — 文件不存在
    set /a FAIL+=1
)

:: 6. 验证 Python import
echo [6] 验证 Agent 模块导入...
cd /d "%PROJECT_ROOT%\backend"
python -c "from devpulse.agents import GitHubTrendingCrawler, TrendingAnalyzer, WeeklyReportSummarizer, ReportPublisher; from devpulse.pipeline import MetaGPTCoordinator; print('    全部导入成功')" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     ✅ 全部模块导入成功
    set /a PASS+=1
) else (
    echo     ❌ 模块导入失败
    set /a FAIL+=1
)

echo.
echo ========================================
echo   检查结果: %PASS% 通过, %FAIL% 失败
echo ========================================

if %FAIL% EQU 0 (
    echo.
    echo   ✅ MetaGPT 集成就绪！
) else (
    echo.
    echo   ❌ MetaGPT 集成未就绪，请修复以上失败项
)

echo.
pause
exit /b %FAIL%