@echo off
echo ===================================================
echo   FULafia DQMS - Setup Script
echo ===================================================
echo.

:: 1. Create Virtual Environment
echo Creating virtual environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment. Make sure Python is installed and in your PATH.
    pause
    exit /b 1
)

:: 2. Activate and install requirements
echo.
echo Installing dependencies from requirements.txt...
call venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 3. Copy env file if not exists
echo.
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
) else (
    echo .env file already exists, skipping copy.
)

:: 4. Initialize Database
echo.
echo Initializing database...
venv\Scripts\python.exe -c "from app import create_app, db; app = create_app(); ctx = app.app_context(); ctx.push(); db.create_all(); print('Database tables created successfully!')"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to initialize database.
    pause
    exit /b 1
)

:: 5. Seed Database
echo.
echo Seeding database with initial university data...
venv\Scripts\python.exe scripts\seed_data.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to seed database.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Setup completed successfully!
echo   Run start.bat to launch the application.
echo ===================================================
pause
