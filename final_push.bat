@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo Final Push to GitHub
echo ========================================
echo.

echo Step 1: Adding all files...
git add .

echo.
echo Step 2: Checking what will be committed...
git status --short

echo.
echo Step 3: Creating commit...
git commit -m "Initial commit: EIM RAG project"

if errorlevel 1 (
    echo Commit failed. Checking status...
    git status
    pause
    exit /b 1
)

echo.
echo Step 4: Setting branch to main...
git branch -M main

echo.
echo Step 5: Setting remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git

echo.
echo Step 6: Pushing to GitHub...
echo.
echo If prompted for authentication:
echo   Username: Allenzhouyujia
echo   Password: Use Personal Access Token (not account password)
echo.
echo Create token at: https://github.com/settings/tokens/new
echo Select: repo (Full control of private repositories)
echo.
pause

git push -u origin main --force

if errorlevel 1 (
    echo.
    echo ========================================
    echo Push failed!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Authentication: Use Personal Access Token as password
    echo 2. Repository doesn't exist: Create it on GitHub first
    echo 3. Network issue: Check your internet connection
    echo.
) else (
    echo.
    echo ========================================
    echo SUCCESS! Code pushed to GitHub!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Create .env file from env.example.txt
    echo 2. Add your new API keys to .env
    echo 3. Revoke old API keys that were exposed
    echo.
)

pause

