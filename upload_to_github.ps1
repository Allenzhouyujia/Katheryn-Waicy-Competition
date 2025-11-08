# PowerShell script to upload to GitHub
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Green
Write-Host "`n检查 Git 状态..." -ForegroundColor Yellow

# Check if files need to be added
$status = git status --short
if (-not $status) {
    Write-Host "没有文件需要提交。检查 .gitignore 设置..." -ForegroundColor Yellow
    
    # Check what files exist
    Write-Host "`n项目文件列表:" -ForegroundColor Cyan
    Get-ChildItem -File | Where-Object { $_.Name -notmatch '^\.' } | Select-Object Name
    
    Write-Host "`n添加所有文件..." -ForegroundColor Yellow
    git add -A
    
    $status = git status --short
    if (-not $status) {
        Write-Host "警告: 所有文件都被 .gitignore 排除了" -ForegroundColor Red
        Write-Host "检查 .gitignore 配置..." -ForegroundColor Yellow
        Get-Content .gitignore | Select-Object -First 25
        exit
    }
}

Write-Host "`n将要提交的文件:" -ForegroundColor Green
git status --short

Write-Host "`n创建提交..." -ForegroundColor Yellow
git commit -m "Initial commit: EIM RAG project - secrets removed"

if ($LASTEXITCODE -ne 0) {
    Write-Host "提交失败" -ForegroundColor Red
    exit
}

Write-Host "`n重命名分支为 main..." -ForegroundColor Yellow
git branch -M main

Write-Host "`n检查远程仓库..." -ForegroundColor Yellow
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "添加远程仓库..." -ForegroundColor Yellow
    git remote add origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git
} else {
    Write-Host "远程仓库已存在: $remote" -ForegroundColor Cyan
    git remote set-url origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git
}

Write-Host "`n推送到 GitHub..." -ForegroundColor Yellow
Write-Host "如果提示需要认证，请输入 GitHub 用户名和 Personal Access Token" -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 成功！代码已推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "`n❌ 推送失败" -ForegroundColor Red
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 需要 GitHub 认证（用户名和 Personal Access Token）" -ForegroundColor Yellow
    Write-Host "2. 仓库不存在或没有权限" -ForegroundColor Yellow
    Write-Host "3. 网络连接问题" -ForegroundColor Yellow
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

