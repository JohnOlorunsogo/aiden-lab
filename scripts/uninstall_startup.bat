@echo off
REM =============================================================================
REM AIDEN Labs - Uninstall Startup Task (Windows)
REM =============================================================================
REM This script removes the AIDEN Labs startup task from Windows Task Scheduler.
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

setlocal

set "TASK_NAME=AIDEN Labs Startup"

echo.
echo =============================================
echo   AIDEN Labs - Uninstalling Startup Task
echo =============================================
echo.

REM Delete the scheduled task
schtasks /delete /tn "%TASK_NAME%" /f

if %errorLevel% equ 0 (
    echo.
    echo =============================================
    echo SUCCESS: Startup task removed!
    echo =============================================
    echo.
    echo AIDEN Labs will no longer start automatically
    echo when you log in to Windows.
    echo.
) else (
    echo.
    echo Note: Task may not have been installed, or
    echo you need to run this script as Administrator.
    echo.
)

pause
