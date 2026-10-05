@echo off
chcp 65001 >nul
title Go Cai Dat Tu Khoi Dong VPS Agent
cd /d "%~dp0"
cls
echo [*] Dang xoa khoi Windows Startup...
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VPS_Agent_AutoStart.vbs" >nul 2>nul

echo [*] Dang xoa khoi Task Scheduler...
schtasks /delete /tn "VPS_Agent_24_7" /f >nul 2>nul

echo.
echo [OK] Da go bo tu khoi dong Agent thanh cong!
pause
