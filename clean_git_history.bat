@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo Cleaning Git History - Removing Secrets
echo ========================================
echo.
echo WARNING: This will rewrite Git history!
echo Make sure you have a backup.
echo.
pause

echo.
echo Step 1: Checking current commits...
git log --oneline --all

echo.
echo Step 2: Removing files with secrets from history...
echo This may take a while...

REM Remove init_knowledge_base.bat from all commits
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch init_knowledge_base.bat" --prune-empty --tag-name-filter cat -- --all

REM Remove start_app.bat from all commits  
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch start_app.bat" --prune-empty --tag-name-filter cat -- --all

REM Remove run_app.py from all commits (old version with secrets)
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch run_app.py" --prune-empty --tag-name-filter cat -- --all

REM Remove remove_secrets_from_git.md (contains example keys)
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch remove_secrets_from_git.md" --prune-empty --tag-name-filter cat -- --all

echo.
echo Step 3: Cleaning up...
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo Step 4: Adding current safe files...
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
git add *.md -f
git add *.ps1
git add *.bat -f
git add data/knowledge_base/ -f

echo.
echo Step 5: Creating new clean commit...
git commit -m "Initial commit: EIM RAG project - clean version without secrets"

echo.
echo Step 6: Force pushing to GitHub...
echo This will overwrite remote history!
pause

git push -u origin main --force

if errorlevel 1 (
    echo.
    echo Push failed. You may need to:
    echo 1. Allow the push in GitHub settings
    echo 2. Or use the unblock URL provided by GitHub
) else (
    echo.
    echo ========================================
    echo Success! Clean history pushed to GitHub
    echo ========================================
)

pause

