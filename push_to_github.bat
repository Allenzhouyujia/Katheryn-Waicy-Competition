@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo Configuring Git user info...
git config user.name "Allenzhouyujia"
git config user.email "allenzhouyujia@gmail.com"

echo.
echo Adding project files...
git add README.md
git add app.py rag_engine.py config.py init_kb.py run_app.py
git add index.html requirements.txt .gitignore
git add canadian-mens-health-foundation_logo.svg
git add init_knowledge_base.bat start_app.bat push_to_github.bat push_to_github.ps1
git add data/knowledge_base/ 2>nul

echo.
echo Creating initial commit...
git commit -m "first commit"
if errorlevel 1 (
    echo Commit failed. Please check the error above.
    pause
    exit /b 1
)

echo.
echo Renaming branch to main...
git branch -M main

echo.
echo Adding remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/Allenzhouyujia/Katheryn-Waicy-Competition.git

echo.
echo Pushing to GitHub...
echo If prompted, enter your GitHub username and Personal Access Token
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed. Please check:
    echo 1. GitHub credentials are correct
    echo 2. Repository exists
    echo 3. Network connection is working
) else (
    echo.
    echo Success! Code has been pushed to GitHub.
)

echo.
pause

