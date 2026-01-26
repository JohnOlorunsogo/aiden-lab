@echo off
REM =============================================================================
REM AIDEN Labs - Install Startup Task (Windows)
REM =============================================================================
REM This script creates a Windows Task Scheduler task to run AIDEN Labs
REM at system startup with administrator privileges.
REM =============================================================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    
    set "SCRIPT=%TEMP%\elevate_%RANDOM%.vbs"
    
    echo Set UAC = CreateObject^("Shell.Application"^) > "%SCRIPT%"
    echo UAC.ShellExecute "%~f0", "", "", "runas", 1 >> "%SCRIPT%"
    
    cscript //nologo "%SCRIPT%"
    del "%SCRIPT%"
    exit /b
)

setlocal enabledelayedexpansion

REM Get the script's directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TASK_NAME=AIDEN Labs Startup"
set "START_SCRIPT=%SCRIPT_DIR%\start_admin.bat"

echo.
echo =============================================
echo    AIDEN Labs - Installing Startup Task
echo =============================================
echo.

REM Check if the start script exists
if not exist "%START_SCRIPT%" (
    echo ERROR: start_admin.bat not found at %START_SCRIPT%
    pause
    exit /b 1
)

REM Delete existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create the scheduled task
echo Creating scheduled task: %TASK_NAME%
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%START_SCRIPT%\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo =============================================
    echo SUCCESS: Startup task installed!
    echo =============================================
    echo.
    echo AIDEN Labs will now start automatically when
    echo you log in to Windows, with admin privileges.
    echo.
    echo Task Name: %TASK_NAME%
    echo Script: %START_SCRIPT%
    echo.
    echo To remove, run: uninstall_startup.bat
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Please run this script as Administrator.
    echo.
)

pause
