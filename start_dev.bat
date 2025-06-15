@echo off
echo 🚀 Dalmatian Pedigree Database (Development Mode)
echo ===============================================
echo 📍 Working directory: %CD%
echo 🔧 Environment: Development
echo.

REM Change to script directory (works from any location)
cd /d "%~dp0"

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo 💡 Activating virtual environment...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ❌ Failed to activate virtual environment!
        echo 💡 Try recreating it: python -m venv venv
        pause
        exit /b 1
    )
    echo ✅ Virtual environment activated: %VIRTUAL_ENV%
) else (
    echo ⚠️  No virtual environment found!
    echo 💡 Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment created and activated
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo 🌐 Starting uvicorn server on http://127.0.0.1:8007
echo 📊 Swagger UI: http://127.0.0.1:8007/docs
echo 📖 ReDoc: http://127.0.0.1:8007/redoc  
echo 🔄 Press Ctrl+C to stop the server
echo.

python main.py

echo.
echo 🛑 Server stopped
pause
