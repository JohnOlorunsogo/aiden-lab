@echo off
REM AIDEN Labs - Install Startup Task (Windows)
REM This script creates a Windows Task Scheduler task to run AIDEN Labs
REM at system startup with administrator privileges.

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

set "SCRIPT_DIR=%~dp0"
set "TASK_NAME=AIDEN Labs Startup"
set "START_SCRIPT=%SCRIPT_DIR%start_admin.bat"

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
