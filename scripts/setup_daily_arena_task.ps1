<#
.SYNOPSIS
    设置 Windows 定时任务：每天自动同步 LMSYS Arena 综合最佳 (Best Overall) 天梯榜并预渲染静态页面

.DESCRIPTION
    此脚本使用 Windows Task Scheduler (schtasks) 注册系统级后台定时任务，
    每天早晨 08:00 (可自定义) 自动执行 scripts/run_daily_arena_sync.bat。
    无需手动打开控制台，支持开机后后台无感自动同步。

.EXAMPLE
    .\scripts\setup_daily_arena_task.ps1
    .\scripts\setup_daily_arena_task.ps1 -Time "09:00"
    .\scripts\setup_daily_arena_task.ps1 -Uninstall
    .\scripts\setup_daily_arena_task.ps1 -RunNow
#>

param(
    [string]$Time = "08:00",
    [switch]$Uninstall,
    [switch]$RunNow,
    [switch]$Status
)

$TaskName = "AINewsRadar_DailyArenaSync"
$WorkspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
$BatPath = Join-Path $WorkspaceDir "scripts\run_daily_arena_sync.bat"

if ($Status) {
    Write-Host "🔍 检查任务状态: $TaskName..." -ForegroundColor Cyan
    schtasks /query /tn $TaskName /fo LIST /v
    exit 0
}

if ($Uninstall) {
    Write-Host "🗑️ 正在移除定时任务: $TaskName..." -ForegroundColor Yellow
    schtasks /delete /tn $TaskName /f
    Write-Host "✓ 定时任务已成功删除！" -ForegroundColor Green
    exit 0
}

if ($RunNow) {
    Write-Host "🚀 正在立即触发一次同步测试..." -ForegroundColor Cyan
    & cmd.exe /c "`"$BatPath`""
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  🏆 LMSYS Arena 综合最佳天梯榜 - Windows 每日自动抓取任务配置" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  • 项目路径: $WorkspaceDir"
Write-Host "  • 批处理执行文件: $BatPath"
Write-Host "  • 触发周期: 每天 $Time"
Write-Host "----------------------------------------------------------"

# 注册 Windows 计划任务
$trArg = "`"$BatPath`""
schtasks /create /tn $TaskName /tr $trArg /sc DAILY /st $Time /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Windows 定时任务注册成功！" -ForegroundColor Green
    Write-Host "  • 任务名称: $TaskName" -ForegroundColor Gray
    Write-Host "  • 自动抓取时间: 每天 $Time" -ForegroundColor Gray
    Write-Host "`n💡 常用管理命令:" -ForegroundColor Yellow
    Write-Host "  - 查看任务状态:  powershell -File .\scripts\setup_daily_arena_task.ps1 -Status"
    Write-Host "  - 立即测试运行:  powershell -File .\scripts\setup_daily_arena_task.ps1 -RunNow"
    Write-Host "  - 删除定时任务:  powershell -File .\scripts\setup_daily_arena_task.ps1 -Uninstall"
} else {
    Write-Host "`n⚠️ 计划任务创建遇到权限限制，如需提升权限请以管理员身份运行 PowerShell 重试。" -ForegroundColor Red
    Write-Host "💡 替代方案：可在后台直接运行 Python 守护进程: python scripts\update_arena_leaderboard.py --daily" -ForegroundColor Yellow
}
