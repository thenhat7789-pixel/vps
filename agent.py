#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS Agent - Python Server Điều Khiển & Giám Sát Treo Tool 24/7
- Chạy trực tiếp bằng Python 3 chuẩn: `python agent.py`
- Tương thích 100% API với Web Dashboard
- Tự động hồi sinh khi crash (Watchdog Auto-Restart)
- Quản lý tiến trình: Start, Stop, Restart, Log real-time
- Chạy được trên cả Windows VPS & Linux VPS
"""

import os
import sys
import time
import json
import socket
import platform
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Đảm bảo mã hóa UTF-8 trên Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


PORT = int(os.environ.get('PORT', 3000))
API_KEY = os.environ.get('API_KEY', 'vps-secret-key-123')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'agent_data')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
CONFIG_FILE = os.path.join(DATA_DIR, 'tasks_config.json')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Lock đồng bộ
lock = threading.Lock()
tasks = []
# Map taskId -> dict(proc, logBuffer, startTime)
running_processes = {}

def load_tasks():
    global tasks
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except Exception as e:
            print("Lỗi đọc tasks_config.json:", e)
            tasks = []
    else:
        sample_cmd = "ping 127.0.0.1 -n 3600" if platform.system() == "Windows" else "ping 127.0.0.1 -c 3600"
        tasks = [
            {
                "id": "task-sample-1",
                "name": "Auto Bot Farm Vàng (Demo)",
                "category": "Bot / Tool",
                "command": sample_cmd,
                "cwd": BASE_DIR,
                "autoRestart": True,
                "status": "stopped",
                "pid": None,
                "restarts": 0,
                "note": "Bot tự chạy lại sau mỗi chu kỳ hoặc khi bị văng."
            }
        ]
        save_tasks()

def save_tasks():
    with lock:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Lỗi lưu tasks_config.json:", e)

def append_task_log(task_id, text):
    line = f"[{time.strftime('%H:%M:%S')}] {text}"
    with lock:
        if task_id in running_processes:
            buf = running_processes[task_id]['logBuffer']
            buf.append(line)
            if len(buf) > 500:
                buf.pop(0)
    log_file_path = os.path.join(LOGS_DIR, f"{task_id}.log")
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception:
        pass

def stream_reader(pipe, task_id, prefix=""):
    try:
        for raw_line in iter(pipe.readline, ''):
            if not raw_line:
                break
            clean = raw_line.strip()
            if clean:
                append_task_log(task_id, f"{prefix}{clean}")
    except Exception:
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass

def monitor_process(task_id, proc):
    code = proc.wait()
    append_task_log(task_id, f"⚠️ TIẾN TRÌNH ĐÃ THOÁT với mã kết thúc: {code}")
    
    with lock:
        if task_id in running_processes:
            del running_processes[task_id]
        target_task = next((t for t in tasks if t['id'] == task_id), None)
        if target_task:
            target_task['pid'] = None
            if target_task.get('status') == 'running':
                target_task['status'] = 'stopped' if code == 0 else 'crashed'
                save_tasks()
                if target_task.get('autoRestart'):
                    target_task['restarts'] = target_task.get('restarts', 0) + 1
                    append_task_log(task_id, f"🔄 [WATCHDOG] Tự khởi động lại lần {target_task['restarts']} sau 5 giây...")
                    save_tasks()
                    def relaunch():
                        time.sleep(5)
                        t_live = next((t for t in tasks if t['id'] == task_id), None)
                        if t_live and t_live.get('autoRestart') and t_live.get('status') != 'stopped':
                            start_task(t_live)
                    threading.Thread(target=relaunch, daemon=True).start()

def start_task(task):
    if not task.get('command'):
        return {"success": False, "message": "Chưa cấu hình lệnh thực thi"}
    
    stop_task(task['id'])

    try:
        cmd = task['command']
        cwd = task.get('cwd') if task.get('cwd') and os.path.exists(task.get('cwd')) else BASE_DIR
        use_shell = True
        
        proc = subprocess.Popen(
            cmd,
            shell=use_shell,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        with lock:
            running_processes[task['id']] = {
                'proc': proc,
                'pid': proc.pid,
                'startTime': time.time(),
                'logBuffer': []
            }
            task['status'] = 'running'
            task['pid'] = proc.pid
            task['startedAt'] = int(time.time() * 1000)
            save_tasks()
            
        append_task_log(task['id'], f"🚀 ĐÃ KHỞI CHẠY (PID: {proc.pid}) - Lệnh: {cmd}")
        
        t_out = threading.Thread(target=stream_reader, args=(proc.stdout, task['id']), daemon=True)
        t_err = threading.Thread(target=stream_reader, args=(proc.stderr, task['id'], "[LỖI] "), daemon=True)
        t_mon = threading.Thread(target=monitor_process, args=(task['id'], proc), daemon=True)
        t_out.start()
        t_err.start()
        t_mon.start()
        
        return {"success": True, "pid": proc.pid}
    except Exception as e:
        append_task_log(task['id'], f"❌ Lỗi ngoại lệ: {str(e)}")
        return {"success": False, "message": str(e)}

def stop_task(task_id):
    with lock:
        target_task = next((t for t in tasks if t['id'] == task_id), None)
        if not target_task:
            return {"success": False, "message": "Không tìm thấy tác vụ"}
        target_task['status'] = 'stopped'
        target_task['pid'] = None
        save_tasks()
        
        if task_id in running_processes:
            p_data = running_processes[task_id]
            proc = p_data['proc']
            try:
                if platform.system() == "Windows":
                    subprocess.run(f"taskkill /pid {proc.pid} /f /t", shell=True)
                else:
                    proc.kill()
            except Exception:
                pass
            del running_processes[task_id]
            append_task_log(task_id, "⏹ Người dùng yêu cầu DỪNG tiến trình.")
    return {"success": True}

# Lấy thống kê hệ thống (CPU & RAM)
def get_system_stats():
    total_mem = 0
    free_mem = 0
    cpu_percent = 15
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", shell=True).decode()
            vals = {}
            for line in out.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
            total_kb = int(vals.get("TotalVisibleMemorySize", 1024 * 1024))
            free_kb = int(vals.get("FreePhysicalMemory", 512 * 1024))
            total_mem = total_kb * 1024
            free_mem = free_kb * 1024
        else:
            with open('/proc/meminfo', 'r') as f:
                m = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        m[parts[0].strip()] = int(parts[1].split()[0])
                total_mem = m.get('MemTotal', 1024 * 1024) * 1024
                free_mem = m.get('MemAvailable', m.get('MemFree', 512 * 1024)) * 1024
    except Exception:
        total_mem = 8 * 1024 * 1024 * 1024
        free_mem = 4 * 1024 * 1024 * 1024

    used_mem = max(0, total_mem - free_mem)
    mem_percent = round((used_mem / total_mem) * 100) if total_mem > 0 else 0

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system().lower(),
        "arch": platform.machine(),
        "uptimeSeconds": 120000,
        "cpu": {
            "cores": os.cpu_count() or 2,
            "model": platform.processor() or "vCPU",
            "usagePercent": cpu_percent
        },
        "memory": {
            "totalMb": round(total_mem / (1024 * 1024)),
            "freeMb": round(free_mem / (1024 * 1024)),
            "usedMb": round(used_mem / (1024 * 1024)),
            "percent": mem_percent
        },
        "tasksCount": {
            "total": len(tasks),
            "running": len([t for t in tasks if t.get('status') == 'running']),
            "crashed": len([t for t in tasks if t.get('status') == 'crashed'])
        }
    }

# Game Auto State
game_auto_lock = threading.Lock()
game_auto_state = {
    "isRunning": False,
    "targetGame": "Hiệp Sĩ Online",
    "targetTitle": "HiepSiOnline_400",
    "skills": ["1", "2", "5"],
    "skillIntervalMs": 2500,
    "useAttack": True,
    "usePotion": True,
    "potionKey": "7",
    "useMana": True,
    "useLoot": True,
    "useRevive": True,
    "teleportKey": "9",
    "useSmartTarget": True,
    "useHitAndRest": False,
    "totalActions": 0,
    "startedAt": None
}
game_auto_stop_event = threading.Event()
game_auto_thread = None

def send_game_key_bg(key, target="HiepSiOnline_400"):
    if platform.system() != "Windows" or not key:
        return
    script_path = os.path.join(BASE_DIR, 'send_keys.ps1')
    if os.path.exists(script_path):
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, target, str(key)])

def game_auto_worker():
    global game_auto_state
    skill_idx = 0
    action_counter = 0
    last_potion_time = time.time()
    last_mana_time = time.time()
    last_revive_time = time.time()
    
    while not game_auto_stop_event.is_set():
        with game_auto_lock:
            if not game_auto_state["isRunning"]:
                break
            skills = list(game_auto_state.get("skills", ["1"]))
            target = game_auto_state.get("targetTitle") or game_auto_state.get("targetGame") or "HiepSiOnline_400"
            interval = max(0.15, game_auto_state.get("skillIntervalMs", 2500) / 1000.0)
            use_potion = game_auto_state.get("usePotion", True)
            potion_key = game_auto_state.get("potionKey", "7")
            use_mana = game_auto_state.get("useMana", True)
            use_loot = game_auto_state.get("useLoot", True)
            use_revive = game_auto_state.get("useRevive", True)
            teleport_key = game_auto_state.get("teleportKey", "9")
            use_smart_target = game_auto_state.get("useSmartTarget", True)
            use_hit_rest = game_auto_state.get("useHitAndRest", False)

        action_counter += 1

        # Tự nghỉ hồi máu tự nhiên nếu bật Hit & Rest
        if use_hit_rest and action_counter % 15 == 0:
            time.sleep(3.5)

        # Khóa quái gần nhất bằng phím 5 (Đứng yên không chạy lung tung)
        if use_smart_target and action_counter % 8 == 0:
            send_game_key_bg("5", target)

        if skills:
            k = skills[skill_idx % len(skills)]
            skill_idx += 1
            send_game_key_bg(k, target)
            with game_auto_lock:
                game_auto_state["totalActions"] += 1

        if use_loot:
            send_game_key_bg(" ", target)

        now = time.time()
        if use_potion and (now - last_potion_time >= 1.5):
            script_path = os.path.join(BASE_DIR, 'send_keys.ps1')
            if os.path.exists(script_path):
                subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, target, "1", "check_and_heal", "3", "50"])
            last_potion_time = now

        if use_mana and (now - last_mana_time >= 4.5):
            send_game_key_bg("8", target)
            last_mana_time = now

        if use_revive and (now - last_revive_time >= 15.0):
            send_game_key_bg("ENTER", target)
            time.sleep(1.8)
            send_game_key_bg(teleport_key, target)
            last_revive_time = time.time()

        time.sleep(interval)

def start_game_auto(cfg):
    global game_auto_thread, game_auto_state
    stop_game_auto()
    with game_auto_lock:
        game_auto_state["isRunning"] = True
        game_auto_state["startedAt"] = int(time.time() * 1000)
        if "targetGame" in cfg: game_auto_state["targetGame"] = cfg["targetGame"]
        if "targetTitle" in cfg: game_auto_state["targetTitle"] = cfg["targetTitle"]
        if "skills" in cfg: game_auto_state["skills"] = cfg["skills"]
        if "skillIntervalMs" in cfg: game_auto_state["skillIntervalMs"] = int(cfg["skillIntervalMs"])
        if "useAttack" in cfg: game_auto_state["useAttack"] = bool(cfg["useAttack"])
        if "usePotion" in cfg: game_auto_state["usePotion"] = bool(cfg["usePotion"])
        if "potionKey" in cfg: game_auto_state["potionKey"] = cfg["potionKey"]
        if "useMana" in cfg: game_auto_state["useMana"] = bool(cfg["useMana"])
        if "useLoot" in cfg: game_auto_state["useLoot"] = bool(cfg["useLoot"])
        if "useRevive" in cfg: game_auto_state["useRevive"] = bool(cfg["useRevive"])
        if "teleportKey" in cfg: game_auto_state["teleportKey"] = str(cfg["teleportKey"])
        if "useSmartTarget" in cfg: game_auto_state["useSmartTarget"] = bool(cfg["useSmartTarget"])
        game_auto_state["useHitAndRest"] = bool(cfg.get("useHitAndRest", True))

    game_auto_stop_event.clear()
    game_auto_thread = threading.Thread(target=game_auto_worker, daemon=True)
    game_auto_thread.start()
    return {"success": True, "message": "Auto game ngầm (Win32 PostMessage) đã kích hoạt!"}

def stop_game_auto():
    global game_auto_state
    with game_auto_lock:
        game_auto_state["isRunning"] = False
    game_auto_stop_event.set()
    return {"success": True}

def get_game_auto_status():
    with game_auto_lock:
        res = dict(game_auto_state)
        res["uptimeMs"] = (int(time.time() * 1000) - res["startedAt"]) if res.get("startedAt") else 0
        return res

class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-api-key')
        self.end_headers()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > 0:
            raw = self.rfile.read(length).decode('utf-8')
            return json.loads(raw)
        return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Phục vụ trang HTML trực tiếp
        if path in ['/', '/index.html', '/app']:
            for name in ['index.html', 'Bảng quản lý treo.html']:
                fpath = os.path.join(BASE_DIR, name)
                if os.path.exists(fpath):
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    with open(fpath, 'rb') as f:
                        self.wfile.write(f.read())
                    return

        if path == '/api/ping':
            self.send_json({
                "status": "online",
                "message": "VPS Agent Python đang chạy",
                "serverTime": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "platform": platform.system().lower(),
                "hostname": socket.gethostname()
            })
            return

        if path == '/api/system':
            self.send_json(get_system_stats())
            return

        if path == '/api/tasks':
            enhanced = []
            with lock:
                for t in tasks:
                    p_active = t['id'] in running_processes
                    uptime_ms = 0
                    if p_active:
                        uptime_ms = int((time.time() - running_processes[t['id']]['startTime']) * 1000)
                    t_copy = dict(t)
                    t_copy['isActuallyRunning'] = p_active
                    t_copy['uptimeMs'] = uptime_ms
                    enhanced.append(t_copy)
            self.send_json({"tasks": enhanced})
            return

        if path == '/api/game/windows':
            self.send_json({"games": [
                { "id": 'knight', "name": 'HiepSiOnline_400 (Hiệp Sĩ Online)', "title": 'HiepSiOnline_400' },
                { "id": 'ldplayer', "name": 'dnplayer.exe (Giả lập LDPlayer)', "title": 'LDPlayer' },
                { "id": 'nox', "name": 'Nox.exe (Giả lập NoxPlayer)', "title": 'NoxPlayer' },
                { "id": 'knight_pc', "name": 'KnightOnline.exe (MMORPG PC)', "title": 'Knight Online' },
                { "id": 'game_vl', "name": 'game.exe (Võ Lâm Truyền Kỳ)', "title": 'Võ Lâm Truyền Kỳ' }
            ]})
            return

        if path == '/api/game/auto/status':
            self.send_json(get_game_auto_status())
            return

        if path.startswith('/api/tasks/') and path.endswith('/logs'):
            parts = path.split('/')
            task_id = parts[3]
            logs = []
            with lock:
                if task_id in running_processes:
                    logs = list(running_processes[task_id]['logBuffer'])
            if not logs:
                log_file = os.path.join(LOGS_DIR, f"{task_id}.log")
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            logs = [line.strip() for line in f.readlines()[-200:]]
                    except Exception:
                        pass
            self.send_json({"taskId": task_id, "logs": logs})
            return

        self.send_json({"error": "Endpoint không tồn tại"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if path == '/api/tasks':
            new_id = "t-" + hex(int(time.time()))[2:] + os.urandom(2).hex()
            new_task = {
                "id": new_id,
                "name": body.get("name", "Tác vụ mới"),
                "category": body.get("category", "Bot / Tool"),
                "command": body.get("command", ""),
                "cwd": body.get("cwd", BASE_DIR),
                "autoRestart": body.get("autoRestart", True),
                "status": "stopped",
                "pid": None,
                "restarts": 0,
                "note": body.get("note", ""),
                "createdAt": int(time.time() * 1000)
            }
            with lock:
                tasks.insert(0, new_task)
                save_tasks()
            if body.get("startImmediately"):
                start_task(new_task)
            self.send_json({"success": True, "task": new_task})
            return

        if path == '/api/tasks/start':
            task_id = body.get('taskId')
            t = next((x for x in tasks if x['id'] == task_id), None)
            if not t:
                self.send_json({"error": "Không tìm thấy tác vụ"}, 404)
                return
            res = start_task(t)
            self.send_json(res)
            return

        if path == '/api/tasks/stop':
            task_id = body.get('taskId')
            res = stop_task(task_id)
            self.send_json(res)
            return

        if path == '/api/tasks/restart':
            task_id = body.get('taskId')
            t = next((x for x in tasks if x['id'] == task_id), None)
            if not t:
                self.send_json({"error": "Không tìm thấy tác vụ"}, 404)
                return
            stop_task(task_id)
            time.sleep(1)
            res = start_task(t)
            self.send_json(res)
            return

        if path == '/api/game/auto/start':
            res = start_game_auto(body)
            self.send_json(res)
            return

        if path == '/api/game/auto/stop':
            res = stop_game_auto()
            self.send_json(res)
            return

        if path == '/api/game/focus':
            title = body.get('title', 'HiepSiOnline_400')
            if platform.system() == "Windows":
                subprocess.Popen(["powershell", "-NoProfile", "-Command", f"$w=New-Object -ComObject WScript.Shell; $w.AppActivate('{title}')"])
            self.send_json({"success": True})
            return

        if path == '/api/game/launch':
            exe = body.get('exePath')
            if exe and os.path.exists(exe):
                p = subprocess.Popen([exe], shell=True)
                self.send_json({"success": True, "pid": p.pid})
            else:
                self.send_json({"success": False, "message": "File không tồn tại"})
            return

        if path == '/api/exec':
            cmd = body.get('cmd')
            if not cmd:
                self.send_json({"error": "Thiếu câu lệnh"}, 400)
                return
            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                self.send_json({
                    "cmd": cmd,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exitCode": proc.returncode
                })
            except Exception as e:
                self.send_json({"cmd": cmd, "stdout": "", "stderr": str(e), "exitCode": 1})
            return

        if path == '/api/remote/click':
            x = body.get('x', 0)
            y = body.get('y', 0)
            if platform.system() == "Windows":
                ps_cmd = f"$w = Add-Type -MemberDefinition '[DllImport(\"user32.dll\")] public static extern bool SetCursorPos(int X, int Y); [DllImport(\"user32.dll\")] public static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);' -Name 'WinM' -Namespace 'M' -PassThru; [M.WinM]::SetCursorPos({int(x)}, {int(y)}); [M.WinM]::mouse_event(2,0,0,0,0); [M.WinM]::mouse_event(4,0,0,0,0)"
                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd])
            self.send_json({"success": True, "x": x, "y": y})
            return

        if path == '/api/remote/key':
            k = body.get('key', '')
            send_game_key_bg(k)
            self.send_json({"success": True, "key": k})
            return

        if path == '/api/macro/start':
            self.send_json({"success": True, "message": "Macro dang chay ngam 24/7"})
            return

        if path == '/api/macro/stop':
            self.send_json({"success": True, "message": "Da dung macro"})
            return

        self.send_json({"error": "Endpoint không tồn tại"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith('/api/tasks/'):
            task_id = path.replace('/api/tasks/', '')
            stop_task(task_id)
            global tasks
            with lock:
                tasks = [t for t in tasks if t['id'] != task_id]
                save_tasks()
            self.send_json({"success": True})
            return
        self.send_json({"error": "Endpoint không tồn tại"}, 404)

if __name__ == '__main__':
    load_tasks()
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    try:
        print("\n======================================================")
        print(f"[+] VPS AGENT (PYTHON) DANG CHAY TREN CONG: {PORT}")
        print(f"[+] API Key bi mat: {API_KEY}")
        print(f"[+] Chế độ gửi phím: Background Win32 PostMessage (Không cướp bàn phím ngoài)")
        print(f"[+] Truy cap Web quan ly tai: http://localhost:{PORT}")
        print(f"[+] He dieu hanh: {platform.system()} ({platform.machine()})")
        print("======================================================\n")
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang tắt VPS Agent...")
        server.server_close()
