@echo off
chcp 65001 >nul
title Tat Agent Chay Ngam
cls
echo [*] Dang dung tat ca tien trinh Agent...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq VPS Control Center*" >nul 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq VPS Control Center*" >nul 2>nul
wmic process where "commandline like '%%agent.js%%' or commandline like '%%agent.py%%'" call terminate >nul 2>nul
echo [OK] Da dung Agent ngam thanh cong!
pause
