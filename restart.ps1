# 重启开发服务器脚本
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Next.js 开发服务器重启脚本" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 停止 Node 进程
Write-Host "[1/3] 停止现有的 Node 进程..." -ForegroundColor Green
$nodeProcess = Get-Process -Name node -ErrorAction SilentlyContinue
if ($nodeProcess) {
    Stop-Process -Name node -Force
    Write-Host "  ✓ Node 进程已停止" -ForegroundColor Green
}
else {
    Write-Host "  ⓘ 没有运行中的 Node 进程" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 2. 清除 .next 缓存
Write-Host ""
Write-Host "[2/3] 清除 .next 缓存..." -ForegroundColor Green
if (Test-Path .next) {
    Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
    Write-Host "  ✓ .next 缓存已清除" -ForegroundColor Green
}
else {
    Write-Host "  ⓘ .next 文件夹不存在，跳过" -ForegroundColor Yellow
}

Start-Sleep -Seconds 1

# 3. 启动开发服务器
Write-Host ""
Write-Host "[3/3] 启动开发服务器..." -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  服务器即将启动..." -ForegroundColor Yellow
Write-Host "  地址: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 停止服务器" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

npm run dev
