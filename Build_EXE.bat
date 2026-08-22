@echo off
title iPortfolio Tracker - Standalone Executable Builder
cd /d "%~dp0"

echo ===================================================
echo   iPortfolio Tracker Executable Builder
echo ===================================================
echo.

echo [1/5] Terminating any active iPortfolioTracker processes...
taskkill /f /im iPortfolioTracker.exe /t 2>nul

echo [2/5] Checking Python Virtual Environment...
if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in venv\Scripts\python.exe
    pause
    exit /b 1
)

echo [3/5] Regenerating App Icons...
venv\Scripts\python.exe create_icon.py
venv\Scripts\python.exe -c "import shutil; shutil.copy('app_icon.ico', 'app/static/app_icon.ico'); shutil.copy('app_icon.png', 'app/static/app_icon.png')"

echo [4/5] Running PyInstaller Build (--onefile --noconsole)...
venv\Scripts\python.exe -m PyInstaller -y --noconfirm --onefile --noconsole --name "iPortfolioTracker" --icon=app_icon.ico --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "Data;Data" --add-data "app_icon.ico;." desktop_app.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED! Please check error output above.
    pause
    exit /b 1
)

echo [5/5] Copying fresh executable to project root...
copy /Y "dist\iPortfolioTracker.exe" "iPortfolioTracker.exe"

echo.
echo ===================================================
echo   BUILD SUCCESSFUL!
echo   Executable created at:
echo   - dist\iPortfolioTracker.exe
echo   - iPortfolioTracker.exe
echo ===================================================
echo.
pause
