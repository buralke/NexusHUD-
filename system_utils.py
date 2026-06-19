import ctypes
import subprocess
import os

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_ram_usage():
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return int(stat.dwMemoryLoad)

def get_cpu_usage():
    try:
        cmd = 'powershell -Command "(Get-CimInstance -ClassName Win32_Processor).LoadPercentage"'
        output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        if output:
            return int(output)
    except Exception:
        pass
    return 12

def execute_system_cmd(action):
    if action == "volume_mute":
        ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
    elif action == "volume_down":
        ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
    elif action == "volume_up":
        ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
    elif action == "media_play_pause":
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
    elif action == "lock":
        ctypes.windll.user32.LockWorkStation()
    elif action == "sleep":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def get_clipboard_text():
    try:
        cmd = 'powershell -Command "Get-Clipboard"'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        return out
    except Exception:
        return ""

def set_clipboard_text(text):
    try:
        p = subprocess.Popen(['powershell', '-Command', 'Set-Clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
        p.communicate(input=text)
        return True
    except Exception:
        return False

# Monitor Brightness Helpers
def get_brightness():
    try:
        cmd = 'powershell -Command "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness"'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        if out:
            return int(out)
    except Exception:
        pass
    return 75

def set_brightness(percent):
    try:
        percent = max(0, min(100, int(percent)))
        cmd = f'powershell -Command "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(0, {percent})"'
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

# Windows Power Plan Helper
def set_power_plan(mode):
    guid_map = {
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "saver": "a1841308-3541-4fab-bc81-f71556f20b4a"
    }
    guid = guid_map.get(mode)
    if guid:
        try:
            subprocess.Popen(f"powercfg /setactive {guid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    return False

def take_screenshot(path):
    try:
        abs_path = os.path.abspath(path).replace('\\', '\\\\')
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms, System.Drawing; "
            "$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$bmp = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height; "
            "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
            "$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $bmp.Size); "
            f"$bmp.Save('{abs_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
            "$graphics.Dispose(); $bmp.Dispose();"
        )
        subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(path)
    except Exception:
        return False

def get_windows_notifications(limit=10):
    import sqlite3
    import shutil
    import re
    from datetime import datetime, timedelta
    
    notifications = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []
    db_path = os.path.join(local_app_data, "Microsoft", "Windows", "Notifications", "wpndatabase.db")
    if not os.path.exists(db_path):
        return []
        
    temp_db = os.path.join(os.getcwd(), "temp_wpn_read.db")
    try:
        shutil.copy2(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        query = """
            SELECT h.PrimaryId, n.Payload, n.ArrivalTime 
            FROM Notification n
            LEFT JOIN NotificationHandler h ON n.HandlerId = h.RecordId
            WHERE n.Type = 'toast'
            ORDER BY n.ArrivalTime DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        for app_id, payload_bytes, arrival_time in rows:
            try:
                payload = payload_bytes.decode('utf-8', errors='ignore')
                texts = re.findall(r'<text[^>]*>(.*?)</text>', payload)
                clean_texts = []
                for t in texts:
                    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
                    clean_texts.append(t.strip())
                
                # Filter out empty texts
                clean_texts = [t for t in clean_texts if t]
                if not clean_texts:
                    continue
                
                # Convert Windows FileTime to readable string (FileTime is UTC)
                try:
                    # 100-nanosecond intervals since 1601-01-01
                    dt = datetime(1601, 1, 1) + timedelta(microseconds=arrival_time // 10)
                    # Convert to local time (Turkey timezone is UTC+3)
                    dt_local = dt + timedelta(hours=3)
                    time_str = dt_local.strftime("%H:%M")
                except Exception:
                    time_str = ""
                
                # Clean app name
                app_name = app_id if app_id else "Bilinmeyen"
                if "!" in app_name:
                    app_name = app_name.split("!")[0]
                if "." in app_name:
                    parts = app_name.split(".")
                    app_name = parts[1] if len(parts) > 1 else parts[0]
                if "_" in app_name:
                    app_name = app_name.split("_")[0]
                
                notifications.append({
                    "app": app_name,
                    "content": " - ".join(clean_texts),
                    "time": time_str
                })
            except Exception:
                pass
        conn.close()
    except Exception:
        pass
    finally:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except Exception:
                pass
    return notifications

def capture_webcam(output_path):
    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows for faster startup
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)  # fallback
        if not cap.isOpened():
            return False
        # Warmup camera
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(output_path, frame)
        cap.release()
        return ret
    except Exception:
        return False
