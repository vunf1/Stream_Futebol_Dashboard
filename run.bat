@echo off
REM Launcher script for Stream Futebol Dashboard
REM Run this batch file from the root directory to start the application.

echo Starting Stream Futebol Dashboard...
echo Working directory: %CD%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please ensure Python is installed and in your PATH.
    pause
    exit /b 1
)

echo Launching application...
python -m src.goal_score

if errorlevel 1 (
    echo Application failed to start. Exit code: %errorlevel%
    pause
    exit /b %errorlevel%
)

echo Application closed.
pause
