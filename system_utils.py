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
