@echo off
title Install CYBERNYTE
cd /d "%~dp0"
python -m pip install -r requirements.txt
echo.
echo Installation complete. Double-click run_cybernyte.bat to start.
pause
