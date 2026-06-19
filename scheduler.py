import json
import os
import time
import uuid
import threading
from datetime import datetime

REMINDERS_FILE = "reminders.json"

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return {}
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_reminders(reminders):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def add_recurrent_reminder(message, interval_minutes):
    reminders = load_reminders()
    rem_id = str(uuid.uuid4())[:8]
    reminders[rem_id] = {
        "id": rem_id,
        "type": "recurrent",
        "message": message,
        "interval_minutes": float(interval_minutes),
        "last_triggered": time.time()
    }
    save_reminders(reminders)
    return rem_id

def add_once_reminder(message, target_time_str, frequency_minutes):
    target_dt = None
    # Support various date/time formats
    for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M"):
        try:
            target_dt = datetime.strptime(target_time_str, fmt)
            break
        except ValueError:
            continue
            
    if not target_dt:
        raise ValueError("Geçersiz tarih/saat formatı. Örn: 22.06.2026 14:00 veya 2026-06-22 14:00")
    
    target_iso = target_dt.strftime("%Y-%m-%d %H:%M")
    
    reminders = load_reminders()
    rem_id = str(uuid.uuid4())[:8]
    reminders[rem_id] = {
        "id": rem_id,
        "type": "once",
        "message": message,
        "target_time": target_iso,
        "frequency_minutes": float(frequency_minutes) if frequency_minutes else 0.0,
        "last_triggered": 0.0,
        "is_active": True
    }
    save_reminders(reminders)
    return rem_id

def delete_reminder(rem_id):
    reminders = load_reminders()
    if rem_id in reminders:
        del reminders[rem_id]
        save_reminders(reminders)
        return True
    return False

def start_scheduler_thread(log_cb, notify_gui_cb, notify_telegram_cb):
    def run():
        while True:
            try:
                reminders = load_reminders()
                now = time.time()
                now_dt = datetime.now()
                changed = False
                
                for rem_id, rem in list(reminders.items()):
                    triggered = False
                    
                    if rem["type"] == "recurrent":
                        interval_sec = rem["interval_minutes"] * 60.0
                        last_trig = rem.get("last_triggered", 0.0)
                        if now - last_trig >= interval_sec:
                            triggered = True
                            rem["last_triggered"] = now
                            changed = True
                            
                    elif rem["type"] == "once":
                        target_str = rem["target_time"]
                        try:
                            target_dt = datetime.strptime(target_str, "%Y-%m-%d %H:%M")
                        except Exception:
                            continue
                        
                        if now_dt >= target_dt:
                            last_trig = rem.get("last_triggered", 0.0)
                            freq_minutes = rem.get("frequency_minutes", 0.0)
                            
                            if last_trig == 0.0:
                                triggered = True
                                rem["last_triggered"] = now
                                changed = True
                            elif freq_minutes > 0.0:
                                if now - last_trig >= freq_minutes * 60.0:
                                    triggered = True
                                    rem["last_triggered"] = now
                                    changed = True
                    
                    if triggered:
                        msg = rem["message"]
                        t_type = "Tekrarlı" if rem["type"] == "recurrent" else "Zamanlanmış"
                        log_cb(f"[HATIRLATICI] {t_type} Hatırlatma: {msg}")
                        
                        notify_gui_cb(rem_id, msg, t_type)
                        notify_telegram_cb(rem_id, msg, t_type)
                
                if changed:
                    save_reminders(reminders)
                    
            except Exception as e:
                log_cb(f"[HATA - SCHEDULER] {str(e)}")
                
            time.sleep(10)
            
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
