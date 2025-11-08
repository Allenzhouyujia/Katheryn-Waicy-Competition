@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo Uploading to GitHub
echo ========================================
echo.

echo Step 1: Adding files...
git add -A
if errorlevel 1 (
    echo Error adding files
    pause
    exit /b 1
)

echo.
echo Step 2: Checking status...
git status --short
if errorlevel 1 (
    echo No files to commit
    pause
    exit /b 1
)

echo.
echo Step 3: Creating commit...
git commit -m "Initial commit: EIM RAG project - secrets removed"
if errorlevel 1 (
    echo Commit failed
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
echo If prompted, enter your GitHub username and Personal Access Token
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed. Possible reasons:
    echo 1. Need GitHub authentication (username and PAT)
    echo 2. Repository doesn't exist or no permission
    echo 3. Network issue
) else (
    echo.
    echo Success! Code has been pushed to GitHub.
)

echo.
pause

