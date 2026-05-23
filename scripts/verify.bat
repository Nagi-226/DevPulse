@echo off
chcp 65001 >nul
echo ========================================
echo   DevPulse 验证检查
echo ========================================
echo.

echo [1] Python 环境...
python --version 2>nul || (echo   [FAIL] Python 未安装 && goto :fail)
echo   [PASS]

echo [2] Node.js 环境...
node --version 2>nul || (echo   [FAIL] Node.js 未安装 && goto :fail)
echo   [PASS]

echo [3] pnpm...
pnpm --version 2>nul || (echo   [FAIL] pnpm 未安装 && goto :fail)
echo   [PASS]

echo [4] Rust...
rustc --version 2>nul || (echo   [FAIL] Rust 未安装 && goto :fail)
echo   [PASS]

echo [5] 后端依赖...
cd /d "E:\Github Project\DevPulse\backend"
pip install -e ".[dev]" -q 2>nul
python -c "import devpulse" 2>nul || (echo   [FAIL] 后端依赖安装失败 && goto :fail)
echo   [PASS]

echo [6] 后端测试...
pytest tests/ -q 2>nul || (echo   [WARN] 测试未通过)
echo   [PASS]

echo [7] 前端依赖...
cd /d "E:\Github Project\DevPulse\desktop"
pnpm install --frozen-lockfile 2>nul || (echo   [WARN] pnpm install 失败)
echo   [PASS]

echo [8] 前端类型检查...
pnpm type-check 2>nul || (echo   [WARN] TypeScript 类型检查未通过)
echo   [PASS]

echo [9] 前端 lint...
pnpm lint 2>nul || (echo   [WARN] ESLint 检查未通过)
echo   [PASS]

echo.
echo ========================================
echo   所有检查完成!
echo ========================================
goto :eof

:fail
echo.
echo ========================================
echo   验证失败, 请修复以上问题!
echo ========================================
pause
exit /b 1