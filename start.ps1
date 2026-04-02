# 获取脚本当前所在目录
$scriptPath = $PSScriptRoot

Write-Host "正在启动 DBMS 项目..." -ForegroundColor Green

# 启动后端服务
$backendDir = Join-Path $scriptPath "backend"
if (Test-Path $backendDir) {
    Write-Host "启动后端服务 (FastAPI)..." -ForegroundColor Cyan
    # 已经修改为使用 uv 启动项目
    $backendCmd = "cd '$backendDir'; uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
} else {
    Write-Host "未找到 backend 目录" -ForegroundColor Red
}

# 启动前端服务
$frontendDir = Join-Path $scriptPath "frontend"
if (Test-Path $frontendDir) {
    Write-Host "启动前端服务 (Vite)..." -ForegroundColor Cyan
    $frontendCmd = "cd '$frontendDir'; npm run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
} else {
    Write-Host "未找到 frontend 目录" -ForegroundColor Red
}

Write-Host "所有服务已触发启动。将打开两个新的终端窗口显示运行日志。" -ForegroundColor Green
Write-Host "按任意键退出当前窗口..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
