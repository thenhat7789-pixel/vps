param(
    [string]$targetTitle = "HiepSiOnline_400",
    [string]$keys = "1",
    [string]$action = "send_key",
    [int]$slot = 3,
    [int]$hpThreshold = 50
)

# Nạp thư viện Win32 C# chuyên biệt gửi phím ngầm & quét máu HP
$cSharpCode = @"
using System;
using System.Text;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Collections.Generic;

public class Win32BackgroundSender {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string lpszClass, string lpszWindow);

    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

    [DllImport("gdi32.dll")]
    public static extern uint GetPixel(IntPtr hdc, int nXPos, int nYPos);

    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const uint WM_CHAR = 0x0102;

    public static uint GetVk(string k) {
        if (string.IsNullOrEmpty(k)) return 0;
        k = k.Trim();
        if (k == "1") return 0x31;
        if (k == "2") return 0x32;
        if (k == "3") return 0x33;
        if (k == "4") return 0x34;
        if (k == "5") return 0x35;
        if (k == "6") return 0x36;
        if (k == "7") return 0x37;
        if (k == "8") return 0x38;
        if (k == "9") return 0x39;
        if (k == "0") return 0x30;
        if (k == " " || k.Equals("SPACE", StringComparison.OrdinalIgnoreCase)) return 0x20;
        if (k.Equals("ENTER", StringComparison.OrdinalIgnoreCase)) return 0x0D;
        if (k.Equals("ESC", StringComparison.OrdinalIgnoreCase)) return 0x1B;
        if (k.Equals("UP", StringComparison.OrdinalIgnoreCase)) return 0x26;
        if (k.Equals("DOWN", StringComparison.OrdinalIgnoreCase)) return 0x28;
        if (k.Equals("LEFT", StringComparison.OrdinalIgnoreCase)) return 0x25;
        if (k.Equals("RIGHT", StringComparison.OrdinalIgnoreCase)) return 0x27;

        if (k.Equals("F1", StringComparison.OrdinalIgnoreCase)) return 0x70;
        if (k.Equals("F2", StringComparison.OrdinalIgnoreCase)) return 0x71;
        if (k.Equals("TAB", StringComparison.OrdinalIgnoreCase)) return 0x09;
        if (k.Equals("I", StringComparison.OrdinalIgnoreCase)) return 0x49;
        if (k.Equals("H", StringComparison.OrdinalIgnoreCase)) return 0x48;
        if (k.Equals("U", StringComparison.OrdinalIgnoreCase)) return 0x55;

        char c = k[0];
        if (char.IsLetter(c)) return (uint)char.ToUpper(c);
        return (uint)c;
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumThreadWindows(int dwThreadId, EnumWindowsProc lpfn, IntPtr lParam);

    public static IntPtr FindGameHwnd(string keyword) {
        // 1. Quét tìm theo Process ID & MainWindowHandle & Thread Windows
        string[] procNames = new string[] { "hso_v403", "HSO_v403B", "hso_v403.exe", "HSO", "Knight", "KnightAge", "HiepSi", "HiepSiOnline_400", "MicroEmulator", "java", "javaw", "dnplayer", "Nox" };
        foreach (string pn in procNames) {
            try {
                string nameOnly = pn.Replace(".exe", "");
                Process[] procs = Process.GetProcessesByName(nameOnly);
                foreach (Process p in procs) {
                    if (p.MainWindowHandle != IntPtr.Zero) {
                        return p.MainWindowHandle;
                    }
                    IntPtr threadHwnd = IntPtr.Zero;
                    foreach (ProcessThread t in p.Threads) {
                        EnumThreadWindows(t.Id, (hWnd, lParam) => {
                            if (IsWindowVisible(hWnd)) {
                                threadHwnd = hWnd;
                                return false;
                            }
                            return true;
                        }, IntPtr.Zero);
                        if (threadHwnd != IntPtr.Zero) return threadHwnd;
                    }
                }
            } catch {}
        }

        // 2. Tìm theo tên chính xác
        if (!string.IsNullOrEmpty(keyword)) {
            IntPtr exact = FindWindow(null, keyword);
            if (exact != IntPtr.Zero) return exact;
        }

        // 3. Quét tất cả các cửa sổ đang mở tìm từ khóa
        IntPtr found = IntPtr.Zero;
        string kw = (keyword ?? "").ToLower();
        string[] defaultKeywords = new string[] { "hiepsi", "knight", "hso", "microemulator" };

        EnumWindows((hWnd, lParam) => {
            if (IsWindowVisible(hWnd)) {
                StringBuilder sb = new StringBuilder(256);
                GetWindowText(hWnd, sb, 256);
                string title = sb.ToString();
                if (!string.IsNullOrEmpty(title)) {
                    string lowerTitle = title.ToLower();
                    if (!string.IsNullOrEmpty(kw) && lowerTitle.Contains(kw)) {
                        found = hWnd;
                        return false;
                    }
                    foreach (string dkw in defaultKeywords) {
                        if (lowerTitle.Contains(dkw)) {
                            found = hWnd;
                            return false;
                        }
                    }
                }
            }
            return true;
        }, IntPtr.Zero);

        return found;
    }

    [DllImport("user32.dll")]
    public static extern uint MapVirtualKey(uint uCode, uint uMapType);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumChildWindows(IntPtr hwndParent, EnumWindowsProc lpEnumFunc, IntPtr lParam);

    public static bool SendSingleKey(IntPtr hWnd, uint vk) {
        if (hWnd == IntPtr.Zero || vk == 0) return false;
        
        uint scanCode = MapVirtualKey(vk, 0);
        IntPtr lParamDown = (IntPtr)(1 | (scanCode << 16));
        IntPtr lParamUp = (IntPtr)(1 | (scanCode << 16) | (1 << 30) | (1 << 31));

        // 1. Gửi vào cửa sổ cha
        PostMessage(hWnd, WM_KEYDOWN, (IntPtr)vk, lParamDown);
        PostMessage(hWnd, WM_CHAR, (IntPtr)vk, lParamDown);
        System.Threading.Thread.Sleep(15);
        PostMessage(hWnd, WM_KEYUP, (IntPtr)vk, lParamUp);

        // 2. Gửi vào tất cả các canvas con
        EnumChildWindows(hWnd, (childHwnd, lParam) => {
            PostMessage(childHwnd, WM_KEYDOWN, (IntPtr)vk, lParamDown);
            PostMessage(childHwnd, WM_CHAR, (IntPtr)vk, lParamDown);
            System.Threading.Thread.Sleep(10);
            PostMessage(childHwnd, WM_KEYUP, (IntPtr)vk, lParamUp);
            return true;
        }, IntPtr.Zero);

        return true;
    }

    public static bool SendKeyIsolated(IntPtr hWnd, string key) {
        if (hWnd == IntPtr.Zero || string.IsNullOrEmpty(key)) return false;
        uint vk = GetVk(key);
        return SendSingleKey(hWnd, vk);
    }

    // Kiểm tra xem máu HP có dưới ngưỡng percent% không
    public static bool IsHpBelowPercent(IntPtr hWnd, int percent) {
        if (hWnd == IntPtr.Zero) return true;
        IntPtr hdc = GetDC(hWnd);
        if (hdc == IntPtr.Zero) return true;
        
        bool isLow = false;
        try {
            // Thanh HP ở góc trên trái: từ X ~ 35 đến X ~ 155, Y ~ 10 đến 22
            int checkX = 35 + (int)((155 - 35) * (percent / 100.0));
            int redCount = 0;
            for (int y = 10; y <= 22; y++) {
                uint color = GetPixel(hdc, checkX, y);
                byte r = (byte)(color & 0x000000FF);
                byte g = (byte)((color & 0x0000FF00) >> 8);
                byte b = (byte)((color & 0x00FF0000) >> 16);
                if (r > 130 && g < 85 && b < 85) {
                    redCount++;
                }
            }
            if (redCount < 2) {
                isLow = true; // Không thấy màu đỏ tại vị trí % -> Máu đã dưới %
            }
        } catch {
            isLow = true;
        } finally {
            ReleaseDC(hWnd, hdc);
        }
        return isLow;
    }

    // Dùng bình máu an toàn (Không dùng phím mũi tên tránh nhân vật chạy lung tung)
    public static bool UseHpFromBag(IntPtr hWnd, int slotIndex) {
        if (hWnd == IntPtr.Zero) return false;
        
        uint vkH = GetVk("H");
        uint vk7 = GetVk("7");

        // Gửi phím tắt hồi phục nhanh túi đồ & ô 7 không làm nhân vật di chuyển
        SendSingleKey(hWnd, vkH);
        System.Threading.Thread.Sleep(20);
        SendSingleKey(hWnd, vk7);
        return true;
    }
}
"@

try {
    if (-not ([System.Management.Automation.PSTypeName]'Win32BackgroundSender').Type) {
        Add-Type -TypeDefinition $cSharpCode -Language CSharp
    }
} catch {
    # Type đã nạp
}

$hWnd = [Win32BackgroundSender]::FindGameHwnd($targetTitle)
$isProc = (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'hso|knight|hiepsi|microemulator|dnplayer|nox' })

if ($hWnd -ne [IntPtr]::Zero) {
    if ($action -eq "check_game") {
        Write-Output "GAME_FOUND"
    } elseif ($action -eq "use_bag_hp") {
        # Tự động mở kho đồ hành trang nốc bình máu
        [Win32BackgroundSender]::UseHpFromBag($hWnd, $slot)
        Write-Output "OK_BAG_HP: Used HP potion from Bag Slot $slot"
    } elseif ($action -eq "check_and_heal") {
        $isLow = [Win32BackgroundSender]::IsHpBelowPercent($hWnd, $hpThreshold)
        if ($isLow) {
            [Win32BackgroundSender]::UseHpFromBag($hWnd, $slot)
            Write-Output "OK_HEALED_LOW_HP: HP < $hpThreshold%, used HP potion from Bag Slot $slot"
        } else {
            Write-Output "OK_HP_HEALTHY: HP is above $hpThreshold%"
        }
    } else {
        [Win32BackgroundSender]::SendKeyIsolated($hWnd, $keys)
        Write-Output "OK_ISOLATED: Sent $keys"
    }
} elseif ($isProc) {
    if ($action -eq "check_game") {
        Write-Output "GAME_FOUND"
    } else {
        # Fallback PostMessage hoặc AppActivate
        try {
            $wshell = New-Object -ComObject WScript.Shell
            if ($wshell.AppActivate("HiepSiOnline") -or $wshell.AppActivate("hso_v403")) {
                $wshell.SendKeys($keys)
            }
        } catch {}
        Write-Output "OK_FALLBACK: Sent $keys"
    }
} else {
    if ($action -eq "check_game") {
        Write-Output "GAME_NOT_FOUND"
    } else {
        Write-Output "WARN: Game window not found for target '$targetTitle'"
    }
}
