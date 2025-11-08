# PowerShell script to push to GitHub
# 使用 UTF-8 编码避免中文乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 获取脚本所在目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Green

# 配置 Git 用户信息
Write-Host "`n配置 Git 用户信息..." -ForegroundColor Yellow
git config user.name "Allenzhouyujia"
git config user.email "allenzhouyujia@gmail.com"

# 删除锁文件（如果存在）
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
    Write-Host "已删除 Git 锁文件" -ForegroundColor Yellow
}

# 添加项目文件
Write-Host "`n添加项目文件..." -ForegroundColor Yellow
git add README.md
git add app.py rag_engine.py config.py init_kb.py run_app.py
git add index.html requirements.txt .gitignore
git add canadian-mens-health-foundation_logo.svg
git add init_knowledge_base.bat start_app.bat push_to_github.bat push_to_github.ps1
git add data/knowledge_base/ -ErrorAction SilentlyContinue

# 检查状态
Write-Host "`n检查 Git 状态..." -ForegroundColor Yellow
$status = git status --short
if ($status) {
    Write-Host $status
} else {
    Write-Host "没有文件需要提交" -ForegroundColor Red
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# 创建提交
Write-Host "`n创建初始提交..." -ForegroundColor Yellow
git commit -m "first commit"

if ($LASTEXITCODE -ne 0) {
    Write-Host "提交失败，请检查错误信息" -ForegroundColor Red
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# 重命名分支为 main
Write-Host "`n重命名分支为 main..." -ForegroundColor Yellow
git branch -M main

# 添加远程仓库
Write-Host "`n添加远程仓库..." -ForegroundColor Yellow
$remoteExists = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "远程仓库已存在，正在更新..." -ForegroundColor Cyan
    git remote set-url origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git
} else {
    git remote add origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git
}

# 推送到 GitHub
Write-Host "`n推送到 GitHub..." -ForegroundColor Yellow
Write-Host "如果提示需要认证，请输入 GitHub 用户名和 Personal Access Token" -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n完成！代码已成功推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "`n推送失败，请检查：" -ForegroundColor Red
    Write-Host "1. GitHub 用户名和密码/Token 是否正确" -ForegroundColor Yellow
    Write-Host "2. 仓库是否存在" -ForegroundColor Yellow
    Write-Host "3. 网络连接是否正常" -ForegroundColor Yellow
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

