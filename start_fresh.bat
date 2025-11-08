@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo Starting Fresh - Removing Git History
echo ========================================
echo.
echo This will delete all Git history and start fresh.
echo Current code is safe (no secrets in files).
echo.
pause

echo.
echo Step 1: Removing .git folder (all history)...
if exist .git (
    rmdir /s /q .git
    echo Git history removed.
) else (
    echo No .git folder found.
)

echo.
echo Step 2: Initializing new Git repository...
git init

echo.
echo Step 3: Configuring Git user...
git config user.name "Allenzhouyujia"
git config user.email "allenzhouyujia@gmail.com"

echo.
echo Step 4: Adding all files...
git add .

echo.
echo Step 5: Checking what will be committed...
git status --short

echo.
echo Step 6: Creating clean commit...
git commit -m "Initial commit: EIM RAG project"

echo.
echo Step 7: Setting branch to main...
git branch -M main

echo.
echo Step 8: Adding remote repository...
git remote add origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git

echo.
echo Step 9: Pushing to GitHub...
echo If prompted, use Personal Access Token as password.
git push -u origin main --force

if errorlevel 1 (
    echo.
    echo ========================================
    echo Push failed!
    echo ========================================
    echo.
    echo If you see authentication error:
    echo 1. Create Personal Access Token:
    echo    https://github.com/settings/tokens/new
    echo    Select: repo (Full control)
    echo.
    echo 2. When prompted for password, use the token
    echo.
    echo If you see secret detection error:
    echo - Check that remove_secrets_from_git.md is not being committed
    echo - Or delete that file first
) else (
    echo.
    echo ========================================
    echo SUCCESS! Code pushed to GitHub!
    echo ========================================
)

pause

