@echo off
echo 🚀 Dalmatian Pedigree Database
echo ============================

REM Change to script directory (works from any location)
cd /d "%~dp0"

REM Try to activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 💡 Activating virtual environment...
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  No virtual environment found - using system Python
    echo 💡 To create venv: python -m venv venv
)

echo.
echo 🌐 Starting server on http://127.0.0.1:8007
echo 🔄 Press Ctrl+C to stop
echo.

python main.py

echo.
echo 🛑 Server stopped
pause
