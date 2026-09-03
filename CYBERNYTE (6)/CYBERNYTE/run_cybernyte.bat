@echo off
title CYBERNYTE Security Command Center
set PYTHONUTF8=1
mode con: cols=150 lines=55 >nul 2>&1
cd /d "%~dp0"
python cybernyte.py
if errorlevel 1 (
  echo.
  echo If Python or packages are missing, run install.bat first.
  pause
)
