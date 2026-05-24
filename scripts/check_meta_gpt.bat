@echo off
:: check_meta_gpt.bat — MetaGPT Integration Readiness Check (v0.0.8)

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"
set PASS=0
set FAIL=0

echo ========================================
echo   MetaGPT Integration Check (v0.0.8)
echo ========================================
echo.

:: 1. Python import test
echo [1] Agent module import...
cd /d "%PROJECT_ROOT%\backend"
python -c "from devpulse.agents import GitHubTrendingCrawler; print('OK')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     [PASS] devpulse.agents
    set /a PASS+=1
) else (
    echo     [FAIL] devpulse.agents
    set /a FAIL+=1
)

:: 2. Check agent files
echo [2] Agent files...
set /a FILE_PASS=0
set /a FILE_FAIL=0
set BACKEND_DIR=%PROJECT_ROOT%\backend\devpulse

if exist "%BACKEND_DIR%\agents\crawler_agent.py" (
    echo     [PASS] agents\crawler_agent.py
    set /a FILE_PASS+=1
) else (
    echo     [FAIL] agents\crawler_agent.py
    set /a FILE_FAIL+=1
)
if exist "%BACKEND_DIR%\agents\analyzer_agent.py" (
    echo     [PASS] agents\analyzer_agent.py
    set /a FILE_PASS+=1
) else (
    echo     [FAIL] agents\analyzer_agent.py
    set /a FILE_FAIL+=1
)
if exist "%BACKEND_DIR%\agents\summarizer_agent.py" (
    echo     [PASS] agents\summarizer_agent.py
    set /a FILE_PASS+=1
) else (
    echo     [FAIL] agents\summarizer_agent.py
    set /a FILE_FAIL+=1
)
if exist "%BACKEND_DIR%\agents\publisher_agent.py" (
    echo     [PASS] agents\publisher_agent.py
    set /a FILE_PASS+=1
) else (
    echo     [FAIL] agents\publisher_agent.py
    set /a FILE_FAIL+=1
)

set /a PASS+=%FILE_PASS%
set /a FAIL+=%FILE_FAIL%

:: 3. Check config switch
echo [3] META_GPT_ENABLED in config.py...
findstr /C:"META_GPT_ENABLED" "%BACKEND_DIR%\config.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     [PASS] META_GPT_ENABLED defined
    set /a PASS+=1
) else (
    echo     [FAIL] META_GPT_ENABLED missing
    set /a FAIL+=1
)

:: 4. Check pipeline switch
echo [4] META_GPT_ENABLED in pipeline.py...
findstr /C:"META_GPT_ENABLED" "%BACKEND_DIR%\services\pipeline.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     [PASS] pipeline.py has MetaGPT switch
    set /a PASS+=1
) else (
    echo     [FAIL] pipeline.py missing MetaGPT switch
    set /a FAIL+=1
)

:: 5. Check coordinator
echo [5] Coordinator file...
if exist "%BACKEND_DIR%\pipeline\meta_gpt_coordinator.py" (
    echo     [PASS] meta_gpt_coordinator.py
    set /a PASS+=1
) else (
    echo     [FAIL] meta_gpt_coordinator.py missing
    set /a FAIL+=1
)

:: 6. Full import verification
echo [6] Full module import...
cd /d "%PROJECT_ROOT%\backend"
set PYTHONPATH=%PROJECT_ROOT%\backend;%PYTHONPATH%
python -c "from devpulse.pipeline.meta_gpt_coordinator import MetaGPTCoordinator; c=MetaGPTCoordinator(); print('import OK')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     [PASS] All modules imported
    set /a PASS+=1
) else (
    echo     [FAIL] Module import failed
    set /a FAIL+=1
)

echo.
echo ========================================
echo   Result: %PASS% passed, %FAIL% failed
echo ========================================

if %FAIL% EQU 0 (
    echo.
    echo   [SUCCESS] MetaGPT integration ready
    echo.
    echo   Launch:
    echo     scripts\dev.bat           — Dev mode (MetaGPT OFF)
    echo     scripts\test_meta_gpt.bat  — MetaGPT mode test
) else (
    echo.
    echo   [FAILED] MetaGPT integration not ready
)

exit /b %FAIL%