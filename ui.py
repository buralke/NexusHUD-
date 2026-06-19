import sys
import os
import json
import subprocess
import webbrowser
import threading
from datetime import datetime
from urllib.parse import quote

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QFrame, QComboBox,
    QSlider, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal

# Import custom modular files
import system_utils
import dialogs
import web_server
import telegram_bot

# Colors & Style Constants
CYAN = "#00f3ff"
DARK_CYAN = "#005f73"
BG = "#060913"
SIDEBAR_BG = "#0d111f"
BORDER_COLOR = "#1a2538"
GREEN = "#00ff66"
RED = "#ff0055"
AMBER = "#ffaa00"

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {BG};
}}
QWidget {{
    background-color: {BG};
    color: #ffffff;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}
QFrame#sidebar {{
    background-color: {SIDEBAR_BG};
    border-right: 1px solid {BORDER_COLOR};
}}
QFrame#input_frame {{
    background-color: {SIDEBAR_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
}}
QFrame#status_bar {{
    background-color: {SIDEBAR_BG};
    border-top: 1px solid {BORDER_COLOR};
}}
QTextEdit#terminal {{
    background-color: {BG};
    border: none;
    color: {CYAN};
}}
QLineEdit {{
    background-color: {SIDEBAR_BG};
    border: none;
    color: #ffffff;
}}
QPushButton {{
    background-color: #14223d;
    border: 1px solid {CYAN};
    border-radius: 4px;
    padding: 6px 12px;
    color: {CYAN};
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {CYAN};
    color: {BG};
}}
QPushButton#sidebar_btn {{
    background-color: {SIDEBAR_BG};
    border: none;
    text-align: left;
    color: {CYAN};
    padding: 4px 8px;
}}
QPushButton#sidebar_btn:hover {{
    background-color: #14223d;
}}
QPushButton#success {{
    background-color: #112519;
    border: 1px solid {GREEN};
    color: {GREEN};
}}
QPushButton#success:hover {{
    background-color: {GREEN};
    color: {BG};
}}
QPushButton#danger {{
    background-color: #2c121c;
    border: 1px solid {RED};
    color: {RED};
}}
QPushButton#danger:hover {{
    background-color: {RED};
    color: {BG};
}}
QComboBox {{
    background-color: {SIDEBAR_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px;
    color: {CYAN};
}}
QComboBox QAbstractItemView {{
    background-color: {SIDEBAR_BG};
    selection-background-color: #14223d;
    selection-color: {CYAN};
    border: 1px solid {BORDER_COLOR};
}}
QSlider::groove:horizontal {{
    border: 1px solid {BORDER_COLOR};
    height: 6px;
    background: {SIDEBAR_BG};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {CYAN};
    border: 1px solid {CYAN};
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}}
"""

# Load command.json
try:
    with open("command.json", "r", encoding="utf-8") as f:
        cmds = json.load(f)
except Exception:
    cmds = {}

# Thread-safe Qt Signal Emitter
class BotSignals(QObject):
    log_signal = Signal(str, str)
    cmd_signal = Signal(str)
    role_signal = Signal(str)
    response_signal = Signal(str)
    reminder_signal = Signal(str, str, str)

signals = BotSignals()

# Global State
roles_dict = {}
last_response = ""

def load_roles():
    global roles_dict
    try:
        if os.path.exists("roles.json"):
            with open("roles.json", "r", encoding="utf-8") as f:
                roles_dict.update(json.load(f))
        else:
            roles_dict.update({
                "Jarvis": "Sen Jarvis'sin, kullanıcının yüksek teknolojili yardımcı yapay zeka asistanısın. Samimi, zeki ve kısa cevaplar verirsin."
            })
    except Exception:
        roles_dict.update({
            "Jarvis": "Sen Jarvis'sin, kullanıcının yüksek teknolojili yardımcı yapay zeka asistanısın. Samimi, zeki ve kısa cevaplar verirsin."
        })

load_roles()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexusHUD v0.2")
        self.resize(920, 600)
        self.setStyleSheet(STYLE_SHEET)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar Frame
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)
        
        lbl_shortcuts = QLabel("// KISAYOLLAR")
        lbl_shortcuts.setStyleSheet(f"color: {DARK_CYAN}; font-weight: bold;")
        sidebar_layout.addWidget(lbl_shortcuts)
        
        # bul command btn
        btn_bul = QPushButton("> bul")
        btn_bul.setObjectName("sidebar_btn")
        btn_bul.clicked.connect(lambda: self.run_cmd("bul"))
        sidebar_layout.addWidget(btn_bul)
        
        # Custom commands scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)
        self.scroll_area.setWidget(self.scroll_widget)
        sidebar_layout.addWidget(self.scroll_area)
        
        # Sidebar shortcut editor buttons
        edit_layout = QHBoxLayout()
        self.btn_add_cmd = QPushButton("+ Ekle")
        self.btn_add_cmd.setObjectName("success")
        self.btn_add_cmd.clicked.connect(self.show_add)
        self.btn_del_cmd = QPushButton("- Sil")
        self.btn_del_cmd.setObjectName("danger")
        self.btn_del_cmd.clicked.connect(self.show_delete)
        edit_layout.addWidget(self.btn_add_cmd)
        edit_layout.addWidget(self.btn_del_cmd)
        sidebar_layout.addLayout(edit_layout)
        
        # System control section
        lbl_sys = QLabel("// SİSTEM KONTROLÜ")
        lbl_sys.setStyleSheet(f"color: {DARK_CYAN}; font-weight: bold;")
        sidebar_layout.addWidget(lbl_sys)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        btn_mute = QPushButton("🔇 Sessiz")
        btn_mute.clicked.connect(lambda: system_utils.execute_system_cmd("volume_mute"))
        btn_play = QPushButton("⏯ Oynat")
        btn_play.clicked.connect(lambda: system_utils.execute_system_cmd("media_play_pause"))
        btn_vdown = QPushButton("🔉 Ses -")
        btn_vdown.clicked.connect(lambda: system_utils.execute_system_cmd("volume_down"))
        btn_vup = QPushButton("🔊 Ses +")
        btn_vup.clicked.connect(lambda: system_utils.execute_system_cmd("volume_up"))
        btn_lock = QPushButton("🔒 Kilitle")
        btn_lock.setObjectName("danger")
        btn_lock.clicked.connect(lambda: system_utils.execute_system_cmd("lock"))
        btn_sleep = QPushButton("💤 Uyku")
        btn_sleep.setObjectName("danger")
        btn_sleep.clicked.connect(lambda: system_utils.execute_system_cmd("sleep"))
        
        grid.addWidget(btn_mute, 0, 0)
        grid.addWidget(btn_play, 0, 1)
        grid.addWidget(btn_vdown, 1, 0)
        grid.addWidget(btn_vup, 1, 1)
        grid.addWidget(btn_lock, 2, 0)
        grid.addWidget(btn_sleep, 2, 1)
        sidebar_layout.addLayout(grid)
        
        # Screen and Power
        lbl_screen = QLabel("// EKRAN & GÜÇ")
        lbl_screen.setStyleSheet(f"color: {DARK_CYAN}; font-weight: bold;")
        sidebar_layout.addWidget(lbl_screen)
        
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Parlaklık:"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(system_utils.get_brightness())
        self.slider.valueChanged.connect(system_utils.set_brightness)
        bright_layout.addWidget(self.slider)
        sidebar_layout.addLayout(bright_layout)
        
        power_layout = QHBoxLayout()
        power_layout.addWidget(QLabel("Güç:"))
        self.power_combo = QComboBox()
        self.power_combo.addItems(["balanced", "high_performance", "saver"])
        self.power_combo.currentTextChanged.connect(system_utils.set_power_plan)
        power_layout.addWidget(self.power_combo)
        sidebar_layout.addLayout(power_layout)
        
        # Extra utils
        btn_analysis = QPushButton("📷 Görsel Analiz Et")
        btn_analysis.clicked.connect(self.show_desktop_image)
        sidebar_layout.addWidget(btn_analysis)
        
        btn_reminders = QPushButton("⏰ Hatırlatıcı Yönetimi")
        btn_reminders.clicked.connect(lambda: dialogs.show_reminder_manager_dialog(self, self.log))
        sidebar_layout.addWidget(btn_reminders)
        
        # System metrics bottom sidebar
        self.lbl_cpu = QLabel("CPU YÜKÜ: --%")
        self.lbl_cpu.setStyleSheet(f"color: {CYAN};")
        self.lbl_ram = QLabel("RAM KULLAN: --%")
        self.lbl_ram.setStyleSheet(f"color: {CYAN};")
        sidebar_layout.addWidget(self.lbl_cpu)
        sidebar_layout.addWidget(self.lbl_ram)
        
        main_layout.addWidget(self.sidebar)
        
        # 2. Main Terminal Panel
        main_panel = QWidget()
        panel_layout = QVBoxLayout(main_panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        panel_layout.setSpacing(6)
        
        # Top bar in Main Panel
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("// TERMİNAL"))
        
        self.btn_api_status = QPushButton("● WIKIPEDIA SEARCH")
        self.btn_api_status.setStyleSheet(f"color: {AMBER}; border: 1px solid {AMBER};")
        self.btn_api_status.clicked.connect(self.show_api_settings)
        top_bar_layout.addWidget(self.btn_api_status)
        
        self.btn_tg_settings = QPushButton("[Telegram Ayarları]")
        self.btn_tg_settings.clicked.connect(lambda: dialogs.show_telegram_settings_dialog(self, self.log))
        top_bar_layout.addWidget(self.btn_tg_settings)
        
        self.lbl_role = QLabel("ROL:")
        self.lbl_role.setStyleSheet(f"color: {DARK_CYAN};")
        self.role_combo = QComboBox()
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        
        self.btn_roles = QPushButton("[Roller]")
        self.btn_roles.clicked.connect(self.show_roles)
        
        top_bar_layout.addWidget(self.lbl_role)
        top_bar_layout.addWidget(self.role_combo)
        top_bar_layout.addWidget(self.btn_roles)
        
        panel_layout.addLayout(top_bar_layout)
        
        # Terminal Output area
        self.terminal = QTextEdit()
        self.terminal.setObjectName("terminal")
        self.terminal.setReadOnly(True)
        panel_layout.addWidget(self.terminal)
        
        # Terminal command input frame
        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.addWidget(QLabel("JARVIS >"))
        
        self.cmd_input = QLineEdit()
        self.cmd_input.returnPressed.connect(self.on_enter)
        input_layout.addWidget(self.cmd_input)
        
        btn_read = QPushButton("🔊 Oku")
        btn_read.clicked.connect(lambda: self.speak_desktop(last_response))
        input_layout.addWidget(btn_read)
        panel_layout.addWidget(input_frame)
        
        # Status Bar bottom
        self.status_bar_frame = QFrame()
        self.status_bar_frame.setObjectName("status_bar")
        self.status_bar_frame.setFixedHeight(26)
        sb_layout = QHBoxLayout(self.status_bar_frame)
        sb_layout.setContentsMargins(10, 0, 10, 0)
        
        self.status_lbl = QLabel("SİSTEM: AKTİF")
        self.status_lbl.setStyleSheet(f"color: {DARK_CYAN};")
        self.clock_lbl = QLabel("")
        self.clock_lbl.setStyleSheet(f"color: {DARK_CYAN};")
        
        sb_layout.addWidget(self.status_lbl)
        sb_layout.addStretch()
        sb_layout.addWidget(self.clock_lbl)
        panel_layout.addWidget(self.status_bar_frame)
        
        main_layout.addWidget(main_panel)
        
        # Register Signals
        signals.log_signal.connect(self.log)
        signals.cmd_signal.connect(self.run_cmd)
        signals.role_signal.connect(self.set_active_role)
        signals.response_signal.connect(self.update_last_response)
        signals.reminder_signal.connect(self.show_scheduled_reminder)
        
        # Timers
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_desktop_stats)
        self.metrics_timer.start(3000)
        
        # Init lists
        self.refresh_sidebar()
        self.update_api_status()
        self.update_desktop_stats()
        
    def update_clock(self):
        self.clock_lbl.setText(datetime.now().strftime("%H:%M:%S"))
        
    def update_desktop_stats(self):
        self.lbl_cpu.setText(f"CPU YÜKÜ: {system_utils.get_cpu_usage()}%")
        self.lbl_ram.setText(f"RAM KULLAN: {system_utils.get_ram_usage()}%")
        
    def log(self, text, tag=""):
        color = CYAN
        if tag == "system":
            color = CYAN
        elif tag == "input":
            color = "#ffffff"
        elif tag == "error":
            color = RED
        elif tag == "warn":
            color = AMBER
            
        formatted_text = f"<span style='color:{color};'>{text.replace(chr(10), '<br>')}</span>"
        self.terminal.append(formatted_text)
        
    def refresh_sidebar(self):
        global cmds
        # Clear old dynamic layout
        for i in reversed(range(self.scroll_layout.count())): 
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
                
        try:
            with open("command.json", "r", encoding="utf-8") as f:
                cmds = json.load(f)
        except Exception as e:
            self.log(f"[SİSTEM HATA] command.json okunamadı: {str(e)}", "error")
            return
            
        for k in cmds:
            btn = QPushButton(f"> {k}")
            btn.setObjectName("sidebar_btn")
            btn.clicked.connect(lambda checked=False, cmd_key=k: self.run_cmd(cmd_key))
            self.scroll_layout.addWidget(btn)
            
    def update_api_status(self):
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY", "")
        if key and key.strip() and not key.startswith("YOUR_GEMINI_API_KEY"):
            import search_bot
            search_bot.configure_api(key)
            self.btn_api_status.setText("● GEMINI API")
            self.btn_api_status.setStyleSheet(f"color: {GREEN}; border: 1px solid {GREEN};")
            
            # Show role controls
            self.lbl_role.show()
            self.role_combo.show()
            self.btn_roles.show()
            
            # Populate role combo
            self.role_combo.blockSignals(True)
            self.role_combo.clear()
            self.role_combo.addItems(list(roles_dict.keys()))
            self.role_combo.setCurrentText("Jarvis")
            self.role_combo.blockSignals(False)
        else:
            import search_bot
            search_bot.configure_api(None)
            self.btn_api_status.setText("● WIKIPEDIA SEARCH")
            self.btn_api_status.setStyleSheet(f"color: {AMBER}; border: 1px solid {AMBER};")
            
            # Hide role controls
            self.lbl_role.hide()
            self.role_combo.hide()
            self.btn_roles.hide()
            
    def show_roles(self):
        dialogs.show_roles_dialog(self, roles_dict, self.refresh_roles, self.log)
        
    def refresh_roles(self):
        load_roles()
        self.role_combo.blockSignals(True)
        current = self.role_combo.currentText()
        self.role_combo.clear()
        self.role_combo.addItems(list(roles_dict.keys()))
        if current in roles_dict:
            self.role_combo.setCurrentText(current)
        self.role_combo.blockSignals(False)
        
    def on_role_changed(self, text):
        self.log(f"[SİSTEM] Aktif yapay zeka rolü değiştirildi: {text}", "system")
        
    def set_active_role(self, role_name):
        if role_name in roles_dict:
            self.role_combo.setCurrentText(role_name)
            
    def show_telegram_settings(self):
        dialogs.show_telegram_settings_dialog(self, self.log)
        
    def show_api_settings(self):
        dialogs.show_api_settings_dialog(self, self.update_api_status, self.log)
        
    def show_add(self):
        dialogs.show_add_dialog(self, self.refresh_sidebar, self.log)
        
    def show_delete(self):
        dialogs.show_delete_dialog(self, cmds, self.refresh_sidebar, self.log)
        
    def show_desktop_image(self):
        dialogs.show_desktop_image_analysis(self, self.role_combo.currentText(), roles_dict, self.log, self.update_last_response)
        
    def show_scheduled_reminder(self, rem_id, msg, t_type):
        import scheduler
        dialogs.show_scheduled_reminder_popup(self, rem_id, msg, t_type, scheduler.delete_reminder)
        
    def on_enter(self):
        text = self.cmd_input.text().strip()
        if text:
            self.run_cmd(text)
            self.cmd_input.clear()
            
    def update_last_response(self, val):
        global last_response
        last_response = val
        
    def speak_desktop(self, text):
        if not text:
            return
        clean_text = text.replace('"', "'").replace("\n", " ")
        ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{clean_text}")'
        subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    def desktop_set_clipboard(self, text):
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
        except Exception as e:
            self.log(f"[HATA] Pano yazma hatası: {str(e)}", "error")
            
    def run_cmd(self, cmd):
        global last_response
        cmd_clean = cmd.strip()
        cmd_lower = cmd_clean.lower()
        
        self.log(f"JARVIS &gt; {cmd_clean}", "input")
        
        # Check for text reminder command
        if cmd_lower.startswith("hatirlat ") or cmd_lower.startswith("uyar "):
            parts = cmd_clean.split(" ", 2)
            if len(parts) >= 3:
                try:
                    mins = float(parts[1])
                    msg = parts[2]
                    import scheduler
                    scheduler.add_recurrent_reminder(msg, mins)
                    self.log(f"[SİSTEM] Tekrarlı hatırlatıcı kuruldu (Her {mins} dk): '{msg}'", "system")
                    return
                except ValueError:
                    pass
                    
        if cmd_lower.startswith("spotify:"):
            q = cmd_clean[8:].strip()
            url = f"https://open.spotify.com/search/{quote(q)}"
            self.log(f"[JARVIS] Spotify'da aranıyor: {q}", "system")
            webbrowser.open(url)
            return
            
        if cmd_lower.startswith("bul "):
            q = cmd_clean[4:].strip()
            self.log(f"[JARVIS] Google'da aranıyor: {q}", "system")
            webbrowser.open(f"https://www.google.com/search?q={quote(q)}")
            return
            
        if cmd_lower == "bul":
            self.log("[SİSTEM] 'bul <arama_terimi>' şeklinde kullanın.", "warn")
            return
            
        # Check in command.json
        if cmd_lower in cmds:
            target = cmds[cmd_lower]
            self.log(f"[SİSTEM] Kısayol çalıştırılıyor: {cmd_lower} -> {target}", "system")
            if target.startswith("http://") or target.startswith("https://"):
                webbrowser.open(target)
            else:
                try:
                    subprocess.Popen(target, shell=True)
                except Exception as e:
                    self.log(f"[HATA] Kısayol çalıştırılamadı: {str(e)}", "error")
            return
            
        # Ask Gemini / Search Wikipedia
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY", "")
        
        if key and key.strip() and not key.startswith("YOUR_GEMINI_API_KEY"):
            # Gemini ask
            self.log("[JARVIS] Düşünüyor...", "system")
            
            def ask_gemini_thread():
                try:
                    from search_bot import ask_gemini
                    active_role = self.role_combo.currentText()
                    system_instruction = roles_dict.get(active_role, None)
                    ans = ask_gemini(cmd_clean, system_instruction=system_instruction)
                    signals.response_signal.emit(ans)
                    signals.log_signal.emit(f"\n{ans}\n", "")
                except Exception as e:
                    signals.log_signal.emit(f"[HATA] Gemini yanıt veremedi: {str(e)}", "error")
                    
            threading.Thread(target=ask_gemini_thread, daemon=True).start()
        else:
            # Wikipedia Search
            self.log("[JARVIS] Wikipedia'da aranıyor...", "system")
            
            def ask_wiki_thread():
                try:
                    from search_bot import search_wikipedia
                    ans = search_wikipedia(cmd_clean)
                    signals.response_signal.emit(ans)
                    signals.log_signal.emit(f"\n{ans}\n", "")
                except Exception as e:
                    signals.log_signal.emit(f"[HATA] Wikipedia aranamadı: {str(e)}", "error")
                    
            threading.Thread(target=ask_wiki_thread, daemon=True).start()

def add_reminder(minutes, message):
    import scheduler
    scheduler.add_recurrent_reminder(message, minutes)

class RoleVarWrapper:
    def __init__(self, combo):
        self.combo = combo
    def get(self):
        return self.combo.currentText()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Check if first launch / guide needed
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if (not key or key.startswith("YOUR_GEMINI") or not key.strip()) and (not token or token.startswith("YOUR_TELEGRAM") or not token.strip()):
        QTimer.singleShot(500, lambda: dialogs.show_welcome_guide(window))
    
    # Start the Web HUD server in a daemon thread
    def start_server_in_thread():
        web_server.start_http_server(
            run_cmd_cb=lambda cmd: signals.cmd_signal.emit(cmd),
            log_cb=lambda text, tag="": signals.log_signal.emit(text, tag),
            roles_dict=roles_dict,
            get_cpu_cb=system_utils.get_cpu_usage,
            get_ram_cb=system_utils.get_ram_usage,
            exec_sys_cb=system_utils.execute_system_cmd,
            update_last_response_cb=window.update_last_response,
            get_clip_cb=system_utils.get_clipboard_text,
            set_clip_cb=window.desktop_set_clipboard,
            get_bright_cb=system_utils.get_brightness,
            set_bright_cb=system_utils.set_brightness,
            set_power_cb=system_utils.set_power_plan,
            add_rem_cb=add_reminder
        )
        
    threading.Thread(target=start_server_in_thread, daemon=True).start()
    
    # Start the Telegram Bot in a daemon thread
    def start_telegram_in_thread():
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        allowed_ids = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
        if token and token.strip():
            telegram_bot.start_telegram_bot(
                token=token,
                allowed_ids_str=allowed_ids,
                log_cb=lambda text, tag="": signals.log_signal.emit(text, tag),
                run_cmd_cb=lambda cmd: signals.cmd_signal.emit(cmd),
                roles_dict=roles_dict,
                role_var=RoleVarWrapper(window.role_combo), # Pass wrapped combo
                update_last_response_cb=window.update_last_response,
                add_reminder_cb=add_reminder,
                set_role_cb=lambda r: signals.role_signal.emit(r)
            )
        else:
            signals.log_signal.emit("[TELEGRAM] Bot aktif değil. .env dosyasında TELEGRAM_BOT_TOKEN tanımlanmalı.", "warn")
            
    threading.Thread(target=start_telegram_in_thread, daemon=True).start()
    
    # Welcome messages
    signals.log_signal.emit("    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗", "system")
    signals.log_signal.emit("    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝", "system")
    signals.log_signal.emit("    ██║███████║██████╔╝██║   ██║██║███████╗", "system")
    signals.log_signal.emit("██   ██║██╔══██║██╔══██║╚██╗ ██╔╝██║╚════██║", "system")
    signals.log_signal.emit("╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║", "system")
    signals.log_signal.emit(" ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝", "system")
    signals.log_signal.emit("", "system")
    signals.log_signal.emit("[SİSTEM] v0.2 Qt6 başlatılıyor...", "system")
    signals.log_signal.emit(f"[SİSTEM] {len(cmds)} komut yüklendi.", "system")
    signals.log_signal.emit("[JARVIS] Hazır. Emredin.", "")
    
    # Start Scheduler
    def notify_telegram_reminder(rem_id, message, t_type):
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        allowed_ids_str = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
        if not token or not allowed_ids_str:
            return
            
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "❌ Kapat (Sil)", "callback_data": f"delrem:{rem_id}"}]
            ]
        }
        
        text_msg = f"🔔 *[HATIRLATICI - {t_type.upper()}]*\n\n{message}"
        
        for val in allowed_ids_str.split(","):
            val = val.strip()
            if val.isdigit():
                chat_id = int(val)
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": text_msg,
                            "parse_mode": "Markdown",
                            "reply_markup": inline_keyboard
                        },
                        timeout=5
                    )
                except Exception:
                    pass

    import scheduler
    scheduler.start_scheduler_thread(
        log_cb=lambda text: signals.log_signal.emit(text, "warn"),
        notify_gui_cb=lambda rem_id, msg, t_type: signals.reminder_signal.emit(rem_id, msg, t_type),
        notify_telegram_cb=notify_telegram_reminder
    )
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
