@echo off
REM AIDEN Labs - Uninstall Startup Task (Windows)
REM This script removes the AIDEN Labs startup task from Windows Task Scheduler.

setlocal

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
