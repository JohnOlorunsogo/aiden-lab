@echo off
REM AIDEN Labs - Admin Startup Script (Windows)
REM This script self-elevates to administrator and starts both services.
REM Usage: Double-click to run with admin privileges

setlocal enabledelayedexpansion

REM Check if running as administrator
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (
    echo Requesting administrator privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

REM Now running as administrator
echo.
echo =============================================
echo    AIDEN Labs - Starting Services (Admin)
echo =============================================
echo.
echo Running with Administrator privileges
echo.

REM Get the script's directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Convert to absolute path
pushd "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"
popd

set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

echo Project Root: %PROJECT_ROOT%
echo Backend Dir:  %BACKEND_DIR%
echo Frontend Dir: %FRONTEND_DIR%
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
    echo Found venv at: %PROJECT_ROOT%\Scripts\activate.bat
) else if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\venv\Scripts\activate.bat"
    echo Found venv at: %PROJECT_ROOT%\venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

REM Build backend command with proper paths
set "BACKEND_CMD=cd /d "%BACKEND_DIR%" && echo Installing Python dependencies... && python -m pip install -r "%BACKEND_DIR%\requirements.txt" && echo. && echo Starting backend server... && python run.py"

if defined VENV_ACTIVATE (
    set "BACKEND_CMD=cd /d "%BACKEND_DIR%" && call "%VENV_ACTIVATE%" && echo Installing Python dependencies... && python -m pip install -r "%BACKEND_DIR%\requirements.txt" && echo. && echo Starting backend server... && python run.py"
)

REM Start Backend in new window
echo.
echo Starting Backend...
start "AIDEN Labs - Backend" cmd /k "%BACKEND_CMD%"
echo Backend starting in new window...

REM Wait a moment for backend to initialize
timeout /t 5 /nobreak > nul

REM Start Frontend in new window
echo Starting Frontend...
set "FRONTEND_CMD=cd /d "%FRONTEND_DIR%" && (if not exist node_modules (echo Installing npm dependencies... && npm install)) && echo. && echo Starting frontend dev server... && npm run dev"
start "AIDEN Labs - Frontend" cmd /k "%FRONTEND_CMD%"
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
