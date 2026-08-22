@echo off
title iPortfolio Tracker Desktop
cd /d "%~dp0"
if exist "dist\iPortfolioTracker\iPortfolioTracker.exe" (
    start "" "dist\iPortfolioTracker\iPortfolioTracker.exe"
) else (
    venv\Scripts\pythonw.exe desktop_app.py
)
