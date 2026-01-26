@echo off
REM =============================================================================
REM AIDEN Labs - Admin Startup Script (Windows)
REM =============================================================================
REM This script self-elevates to administrator and starts both services.
REM Usage: Double-click to run with admin privileges
REM =============================================================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    
    REM Create a temporary VBScript to elevate privileges
    set "SCRIPT=%TEMP%\elevate_%RANDOM%.vbs"
    
    echo Set UAC = CreateObject^("Shell.Application"^) > "%SCRIPT%"
    echo UAC.ShellExecute "%~f0", "", "", "runas", 1 >> "%SCRIPT%"
    
    cscript //nologo "%SCRIPT%"
    del "%SCRIPT%"
    exit /b
)

REM Now running as administrator
setlocal enabledelayedexpansion

REM Get the script's directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%") do set "PROJECT_ROOT=%%~dpI"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

echo.
echo =============================================
echo    AIDEN Labs - Starting Services (Admin)
echo =============================================
echo.
echo Running with Administrator privileges
echo.

REM Check if directories exist
if not exist "%BACKEND_DIR%" (
    echo ERROR: Backend directory not found at %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo ERROR: Frontend directory not found at %FRONTEND_DIR%
    pause
    exit /b 1
)

REM Check for virtual environment
set "VENV_ACTIVATE="
if exist "%PROJECT_ROOT%\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\Scripts\activate.bat"
) else if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\venv\Scripts\activate.bat"
)

REM Start Backend in new window
echo Starting Backend...
if defined VENV_ACTIVATE (
    start "AIDEN Labs - Backend" cmd /k "cd /d "%BACKEND_DIR%" && call "%VENV_ACTIVATE%" && echo Checking dependencies... && pip install -q -r requirements.txt 2>nul && python run.py"
) else (
    start "AIDEN Labs - Backend" cmd /k "cd /d "%BACKEND_DIR%" && echo Checking dependencies... && pip install -q -r requirements.txt 2>nul && python run.py"
)
echo Backend starting in new window...

REM Wait a moment for backend to initialize
timeout /t 2 /nobreak > nul

REM Start Frontend in new window
echo Starting Frontend...
start "AIDEN Labs - Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && if not exist node_modules (echo Installing dependencies... && npm install) && npm run dev"
echo Frontend starting in new window...

echo.
echo =============================================
echo Services are starting in separate windows:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo =============================================
echo.
echo Close this window or press any key to exit.
echo (The services will continue running in their windows)
echo.

pause > nul
