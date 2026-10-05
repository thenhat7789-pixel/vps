@echo off
chcp 65001 >nul
title Cai Dat Tu Dong Chay VPS Agent 24/7
cd /d "%~dp0"
cls

echo ===============================================================
echo     [+] CÀI ĐẶT TỰ ĐỘNG KHỞI CHẠY VPS AGENT (24/7 KHÔNG CẦN BẬT TAY)
echo ===============================================================
echo.
echo Hệ thống sẽ đăng ký Agent tự chạy ngầm cùng Windows:
echo  1. VPS vừa bật / Reboot là Web Agent tự chạy ngay lập tức.
echo  2. Không cần mở cửa sổ đen CMD (chạy ngầm 100%%).
echo  3. Bất cứ khi nào vào Tên Miền / IP là Web hoạt động ngay!
echo.
echo ---------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
set "VBS_FILE=%SCRIPT_DIR%start_agent_hidden.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_TARGET=%STARTUP_FOLDER%\VPS_Agent_AutoStart.vbs"

:: 1. Copy file VBS vào thư mục Startup của Windows
echo [*] Dang tao loi tat vao thu muc Windows Startup...
copy /y "%VBS_FILE%" "%STARTUP_TARGET%" >nul
if %errorlevel% equ 0 (
    echo [OK] Da them thanh cong vao Windows Startup!
) else (
    echo [!] Khong the copy vao Startup folder, tiep tuc voi Task Scheduler...
)

:: 2. Đăng ký Windows Task Scheduler (Chạy ở chế độ System/Logon)
echo [*] Dang tao Task Scheduler: VPS_Agent_24_7...
schtasks /create /tn "VPS_Agent_24_7" /tr "wscript.exe \"%VBS_FILE%\"" /sc onlogon /rl highest /f >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Da dang ky Task Scheduler thanh cong (Chay quyen cao nhat khi mo VPS)!
) else (
    echo [!] Ban can chay file nay voi quyen Run as Administrator de kich hoat Task Scheduler.
)

:: 3. Khởi chạy ngầm ngay bây giờ
echo.
echo [*] Dang khoi chay Agent ngam ngay lap tuc...
wscript.exe "%VBS_FILE%"

echo.
echo ===============================================================
echo [THANH CONG] CAI DAT HOAN TAT!
echo ===============================================================
echo - Bay gio Agent da chay ngam 24/7.
echo - Khi bat VPS / Mo ten mien la Web Controller san sang ngay!
echo.
echo De tat Agent chay ngam, hay chay file: tat_agent_ngam.bat
echo De go bo tu khoi dong, hay chay file: go_cai_dat_tu_khoi_dong.bat
echo ===============================================================
echo.
pause
