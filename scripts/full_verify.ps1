<#
.SYNOPSIS
    DevPulse 全量验证脚本 (PowerShell 增强版)
.DESCRIPTION
    比 verify.bat 增强的功能：
    - 彩色输出 (绿色 PASS / 红色 FAIL / 黄色 WARN)
    - 后端启动 + curl 健康检查
    - 前端 dev server 启动 + curl 页面检查
    - 自动清理测试进程
.NOTES
    版本: v0.0.9
    要求: PowerShell 5.1+
#>

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PASS = 0
$FAIL = 0
$WARN = 0
$TOTAL = 11  # 9 basic + 2 health checks
$BackendProcess = $null
$FrontendProcess = $null

function Write-Pass { Write-Host "  [PASS]" -ForegroundColor Green }
function Write-Fail { Write-Host "  [FAIL]" -ForegroundColor Red }
function Write-Warn { Write-Host "  [WARN]" -ForegroundColor Yellow }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DevPulse 全量验证 (PowerShell 增强版)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 1. Python 环境检查
# ============================================================
Write-Host "[1/11] Python 环境检查 ..."
try {
    $v = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $v"
        Write-Pass; $PASS++
    } else {
        Write-Fail; $FAIL++
    }
} catch {
    Write-Host "  Python 未安装"
    Write-Fail; $FAIL++
}
Write-Host ""

# ============================================================
# 2. Node.js 环境检查
# ============================================================
Write-Host "[2/11] Node.js 环境检查 ..."
try {
    $v = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $v"
        Write-Pass; $PASS++
    } else {
        Write-Fail; $FAIL++
    }
} catch {
    Write-Host "  Node.js 未安装"
    Write-Fail; $FAIL++
}
Write-Host ""

# ============================================================
# 3. Rust 环境检查（不阻塞）
# ============================================================
Write-Host "[3/11] Rust 环境检查 ..."
try {
    $v = rustc --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $v"
        Write-Pass; $PASS++
    } else {
        Write-Warn "  Rust 未安装 (仅 Tauri 打包需要，不阻塞)"
        Write-Warn; $WARN++; $PASS++
    }
} catch {
    Write-Warn "  Rust 未安装 (仅 Tauri 打包需要，不阻塞)"
    Write-Warn; $WARN++; $PASS++
}
Write-Host ""

# ============================================================
# 4. 后端依赖安装
# ============================================================
Write-Host "[4/11] 后端依赖安装 ..."
Set-Location "$ProjectRoot\backend"
pip install -e ".[dev]" -q 2>&1 | Out-Null
python -c "import devpulse" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Pass; $PASS++
} else {
    Write-Fail; $FAIL++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 5. 前端依赖安装
# ============================================================
Write-Host "[5/11] 前端依赖安装 ..."
Set-Location "$ProjectRoot\desktop"
pnpm install --frozen-lockfile 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warn "  pnpm install 失败，尝试 npm install ..."
    npm install 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Pass; $PASS++
    } else {
        Write-Fail; $FAIL++
    }
} else {
    Write-Pass; $PASS++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 6. 后端测试
# ============================================================
Write-Host "[6/11] 后端测试 (pytest) ..."
Set-Location "$ProjectRoot\backend"
python -m pytest tests/ -q 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Pass; $PASS++
} else {
    Write-Fail; $FAIL++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 7. 后端 lint (ruff)
# ============================================================
Write-Host "[7/11] 后端 lint (ruff) ..."
Set-Location "$ProjectRoot\backend"
ruff check devpulse/ tests/ 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Pass; $PASS++
} else {
    Write-Fail; $FAIL++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 8. 前端类型检查 (tsc --noEmit)
# ============================================================
Write-Host "[8/11] 前端类型检查 (tsc --noEmit) ..."
Set-Location "$ProjectRoot\desktop"
npx tsc --noEmit 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Pass; $PASS++
} else {
    Write-Fail; $FAIL++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 9. 前端构建
# ============================================================
Write-Host "[9/11] 前端构建 (npm run build) ..."
Set-Location "$ProjectRoot\desktop"
npm run build 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Pass; $PASS++
} else {
    Write-Fail; $FAIL++
}
Set-Location $ProjectRoot
Write-Host ""

# ============================================================
# 10. 后端启动 + curl 健康检查
# ============================================================
Write-Host "[10/11] 后端启动 + 健康检查 ..."

$BackendProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "devpulse.main:app", "--port", "8000" `
    -WorkingDirectory "$ProjectRoot\backend" `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $json = $response.Content | ConvertFrom-Json
        Write-Host "  状态: $($json.status), 版本: $($json.version)"
        Write-Pass; $PASS++
    } else {
        Write-Fail; $FAIL++
    }
} catch {
    Write-Host "  无法连接到后端健康检查端点"
    Write-Fail; $FAIL++
}

Write-Host ""

# ============================================================
# 11. 前端 dev server 启动 + 页面检查
# ============================================================
Write-Host "[11/11] 前端 dev server 启动 + 页面检查 ..."

$FrontendProcess = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory "$ProjectRoot\desktop" `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://localhost:1420" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  前端页面可访问 (HTTP 200)"
        Write-Pass; $PASS++
    } else {
        Write-Host "  前端返回 HTTP $($response.StatusCode)"
        Write-Fail; $FAIL++
    }
} catch {
    Write-Host "  无法连接到前端页面"
    Write-Fail; $FAIL++
}

Write-Host ""

# ============================================================
# 清理测试进程
# ============================================================
Write-Host "清理测试进程 ..."
if ($BackendProcess -and !$BackendProcess.HasExited) {
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "  已停止后端进程 (PID: $($BackendProcess.Id))"
}
if ($FrontendProcess -and !$FrontendProcess.HasExited) {
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    # 同时清理 Vite 子进程（如果 npm 已退出但 vite 还在）
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*vite*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  已停止前端进程 (PID: $($FrontendProcess.Id))"
}
Write-Host ""

# ============================================================
# 汇总输出
# ============================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  验证完成: $PASS/$TOTAL 通过" -ForegroundColor $(if ($FAIL -gt 0) { "Yellow" } else { "Green" })
if ($FAIL -gt 0) {
    Write-Host "  失败项: $FAIL 项需要修复" -ForegroundColor Red
}
if ($WARN -gt 0) {
    Write-Host "  警告项: $WARN 项 (不阻塞)" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan

if ($FAIL -gt 0) {
    exit 1
}