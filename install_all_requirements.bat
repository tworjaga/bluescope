@echo off
REM Change to the script's directory
cd /d "%~dp0"

echo ========================================
echo BlueScope - Complete Installation
echo ========================================
echo.
echo [INFO] Working directory: %CD%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run this first: python -m venv venv
    pause
    exit /b 1
)

echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Installing minimal requirements...
pip install -r requirements-minimal.txt

echo.
echo [4/4] Installing full requirements (this may take 5-10 minutes)...
pip install -r requirements.txt

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Installed packages:
pip list
echo.
echo To start BlueScope:
echo   1. Double-click: start-simple.bat
echo   2. Or run: python main.py
echo.
pause
