@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo Fixing Git Upload
echo ========================================
echo.

echo Step 1: Checking current status...
git status

echo.
echo Step 2: Adding specific files...
git add README.md
git add app.py
git add rag_engine.py
git add config.py
git add init_kb.py
git add run_app.py
git add index.html
git add requirements.txt
git add .gitignore
git add env.example.txt
git add canadian-mens-health-foundation_logo.svg
git add mcp.json.example
git add *.md
git add *.ps1
git add *.bat
git add data/knowledge_base/ -f

echo.
echo Step 3: Checking what will be committed...
git status --short

echo.
echo Step 4: Creating commit...
git commit -m "Initial commit: EIM RAG project - secrets removed"

if errorlevel 1 (
    echo.
    echo Commit failed. Checking why...
    git status
    pause
    exit /b 1
)

echo.
echo Step 5: Setting branch to main...
git branch -M main

echo.
echo Step 6: Pushing to GitHub...
echo If prompted for authentication:
echo - Username: Allenzhouyujia
echo - Password: Use Personal Access Token (not account password)
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo Push failed!
    echo ========================================
    echo.
    echo Possible solutions:
    echo 1. Create Personal Access Token:
    echo    https://github.com/settings/tokens/new
    echo    Select: repo (Full control of private repositories)
    echo.
    echo 2. Use token as password when prompted
    echo.
    echo 3. Or use SSH instead:
    echo    git remote set-url origin git@github.com:Allenzhouyujia/Katheryn-Waicy-Competition.git
    echo.
) else (
    echo.
    echo ========================================
    echo Success! Code pushed to GitHub
    echo ========================================
)

pause

