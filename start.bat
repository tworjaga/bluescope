@echo off
REM BlueScope - Simple Quick Start
REM No dependency checking - just install and run

REM Change to the script's directory
cd /d "%~dp0"

echo ============================================================
echo  BlueScope - Enterprise Bluetooth Monitoring Platform
echo ============================================================
echo.
echo [INFO] Working directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.11 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created!
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo.

REM Always try to install/upgrade dependencies
echo [INFO] Installing/updating dependencies...
echo [INFO] This will install minimal dependencies for quick start...
echo.
python -m pip install --upgrade pip --quiet
pip install -r requirements-minimal.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    echo.
    echo Try running manually:
    echo   venv\Scripts\activate
    echo   pip install -r requirements-minimal.txt
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies ready!
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" (
    mkdir logs
)

REM Launch BlueScope
echo ============================================================
echo  Launching BlueScope GUI...
echo ============================================================
echo.
echo Press Ctrl+C to stop the application
echo.

python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] BlueScope failed to start!
    echo.
    echo Check the error above or see logs\bluescope.log for details
    echo.
    echo Common issues:
    echo   - Missing dependencies: Run "pip install -r requirements-minimal.txt"
    echo   - Import errors: Check if PyQt6 is installed
    echo   - Python version: Requires Python 3.11+
    echo.
    pause
    exit /b 1
)

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat

echo.
echo ============================================================
echo  BlueScope has been closed
echo ============================================================
pause
