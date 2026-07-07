@echo off
echo ===================================================
echo   FULafia DQMS - Start Script
echo ===================================================
echo.

if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting the Flask application server...
echo The application will be accessible at http://localhost:5000
echo.
venv\Scripts\python.exe run.py
pause
