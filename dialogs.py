import os
import json
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QListWidget, QCheckBox, QRadioButton,
    QFileDialog, QButtonGroup, QWidget
)
from PySide6.QtCore import Qt

# Style Constants
CYAN = "#00f3ff"
DARK_CYAN = "#005f73"
BG = "#060913"
SIDEBAR_BG = "#0d111f"
BORDER_COLOR = "#1a2538"
GREEN = "#00ff66"
RED = "#ff0055"
AMBER = "#ffaa00"

DIALOG_STYLE = f"""
QDialog {{
    background-color: {BG};
    border: 2px solid {CYAN};
}}
QWidget {{
    background-color: {BG};
    color: #ffffff;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}
QLabel {{
    color: {CYAN};
    font-weight: bold;
}}
QLineEdit, QTextEdit {{
    background-color: {SIDEBAR_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {CYAN};
}}
QListWidget {{
    background-color: {SIDEBAR_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    color: #ffffff;
}}
QListWidget::item:selected {{
    background-color: #14223d;
    color: {CYAN};
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
QPushButton#danger {{
    background-color: #2c121c;
    border: 1px solid {RED};
    color: {RED};
}}
QPushButton#danger:hover {{
    background-color: {RED};
    color: {BG};
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
QCheckBox, QRadioButton {{
    color: #ffffff;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    border: 1px solid {BORDER_COLOR};
    width: 12px;
    height: 12px;
    background: {SIDEBAR_BG};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {CYAN};
    border: 1px solid {CYAN};
}}
"""

def show_roles_dialog(parent, roles_dict, refresh_roles_menu_cb, log_cb):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Rol Yönetimi")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(520, 360)
    
    layout = QHBoxLayout(dialog)
    
    # Left container (List of roles)
    left_layout = QVBoxLayout()
    left_layout.addWidget(QLabel("MEVCUT ROLLER"))
    
    listbox = QListWidget()
    left_layout.addWidget(listbox)
    
    def populate_listbox():
        listbox.clear()
        for r_name in roles_dict:
            listbox.addItem(r_name)
    populate_listbox()
    
    # Right container (Form)
    right_layout = QVBoxLayout()
    right_layout.addWidget(QLabel("YENİ ROL ADI"))
    name_entry = QLineEdit()
    right_layout.addWidget(name_entry)
    
    right_layout.addWidget(QLabel("SİSTEM TALİMATI"))
    instruction_text = QTextEdit()
    right_layout.addWidget(instruction_text)
    
    def add_new_role():
        name = name_entry.text().strip()
        instr = instruction_text.toPlainText().strip()
        if not name or not instr:
            return
            
        try:
            r_dict = {}
            if os.path.exists("roles.json"):
                with open("roles.json", "r", encoding="utf-8") as f:
                    r_dict = json.load(f)
            r_dict[name] = instr
            with open("roles.json", "w", encoding="utf-8") as f:
                json.dump(r_dict, f, indent=2, ensure_ascii=False)
            
            roles_dict[name] = instr
            refresh_roles_menu_cb()
            populate_listbox()
            name_entry.clear()
            instruction_text.clear()
            log_cb(f"[SİSTEM] Yeni rol eklendi: {name}", "system")
        except Exception as e:
            log_cb(f"[HATA] Rol eklenemedi: {str(e)}", "error")
            
    def delete_selected_role():
        current_item = listbox.currentItem()
        if not current_item:
            return
        r_name = current_item.text()
        if r_name == "Jarvis":
            return
            
        try:
            r_dict = {}
            if os.path.exists("roles.json"):
                with open("roles.json", "r", encoding="utf-8") as f:
                    r_dict = json.load(f)
            if r_name in r_dict:
                del r_dict[r_name]
            with open("roles.json", "w", encoding="utf-8") as f:
                json.dump(r_dict, f, indent=2, ensure_ascii=False)
                
            if r_name in roles_dict:
                del roles_dict[r_name]
            refresh_roles_menu_cb()
            populate_listbox()
            log_cb(f"[SİSTEM] Rol silindi: {r_name}", "warn")
        except Exception as e:
            log_cb(f"[HATA] Rol silinemedi: {str(e)}", "error")

    btn_add = QPushButton("Rolü Ekle")
    btn_add.setObjectName("success")
    btn_add.clicked.connect(add_new_role)
    right_layout.addWidget(btn_add)
    
    btn_del = QPushButton("Seçileni Sil")
    btn_del.setObjectName("danger")
    btn_del.clicked.connect(delete_selected_role)
    left_layout.addWidget(btn_del)
    
    layout.addLayout(left_layout)
    layout.addLayout(right_layout)
    
    dialog.exec()

def show_api_settings_dialog(parent, update_api_status_cb, log_cb):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Gemini API Ayarları")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(400, 200)
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("GEMINI API ANAHTARI"))
    
    from dotenv import load_dotenv
    load_dotenv()
    current_key = os.getenv("GEMINI_API_KEY", "")
    if current_key.startswith("YOUR_GEMINI_API_KEY"):
        current_key = ""
        
    key_entry = QLineEdit()
    key_entry.setEchoMode(QLineEdit.Password)
    key_entry.setText(current_key)
    layout.addWidget(key_entry)
    
    show_cb = QCheckBox("Anahtarı Göster")
    def toggle_show(state):
        if state == Qt.Checked.value or state == 2:
            key_entry.setEchoMode(QLineEdit.Normal)
        else:
            key_entry.setEchoMode(QLineEdit.Password)
    show_cb.stateChanged.connect(toggle_show)
    layout.addWidget(show_cb)
    
    def save_api_key():
        new_key = key_entry.text().strip()
        try:
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    env_lines = f.readlines()
            
            key_found = False
            for idx, line in enumerate(env_lines):
                if line.strip().startswith("GEMINI_API_KEY="):
                    env_lines[idx] = f"GEMINI_API_KEY={new_key}\n"
                    key_found = True
                    break
            
            if not key_found:
                env_lines.append(f"GEMINI_API_KEY={new_key}\n")
                
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(env_lines)
                
            import search_bot
            search_bot.configure_api(new_key)
            
            update_api_status_cb()
            log_cb("[SİSTEM] Gemini API anahtarı güncellendi.", "system")
            dialog.accept()
        except Exception as e:
            log_cb(f"[HATA] API anahtarı kaydedilemedi: {str(e)}", "error")

    btn_save = QPushButton("Kaydet")
    btn_save.clicked.connect(save_api_key)
    layout.addWidget(btn_save)
    
    dialog.exec()

def show_add_dialog(parent, refresh_sidebar_cb, log_cb):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Komut Ekle")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(400, 220)
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("KISAYOL ADI (örn: google)"))
    key_entry = QLineEdit()
    layout.addWidget(key_entry)
    
    layout.addWidget(QLabel("KOMUT / URL VEYA DOSYA YOLU"))
    val_layout = QHBoxLayout()
    val_entry = QLineEdit()
    val_layout.addWidget(val_entry)
    
    def select_file():
        file_path, _ = QFileDialog.getOpenFileName(dialog, "Dosya veya Uygulama Seç", "", "Tüm Dosyalar (*.*);;Uygulamalar (*.exe);;Kısayollar (*.lnk)")
        if file_path:
            val_entry.setText(f'"{os.path.normpath(file_path)}"')
            
    btn_browse = QPushButton("Gözat...")
    btn_browse.clicked.connect(select_file)
    val_layout.addWidget(btn_browse)
    layout.addLayout(val_layout)
    
    def save_cmd():
        k = key_entry.text().strip().lower()
        v = val_entry.text().strip()
        if not k or not v:
            return
            
        try:
            current_cmds = {}
            if os.path.exists("command.json"):
                with open("command.json", "r", encoding="utf-8") as f:
                    current_cmds = json.load(f)
            current_cmds[k] = v
            with open("command.json", "w", encoding="utf-8") as f:
                json.dump(current_cmds, f, indent=2, ensure_ascii=False)
            
            refresh_sidebar_cb()
            log_cb(f"[SİSTEM] Yeni komut eklendi: {k}", "system")
            dialog.accept()
        except Exception as e:
            log_cb(f"[HATA] Komut eklenemedi: {str(e)}", "error")

    btn_save = QPushButton("Kaydet")
    btn_save.setObjectName("success")
    btn_save.clicked.connect(save_cmd)
    layout.addWidget(btn_save)
    
    dialog.exec()

def show_delete_dialog(parent, cmds, refresh_sidebar_cb, log_cb):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Komut Sil")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(300, 250)
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("SİLİNECEK KOMUTU SEÇİN"))
    
    listbox = QListWidget()
    for k in cmds:
        listbox.addItem(k)
    layout.addWidget(listbox)
    
    def delete_cmd():
        current_item = listbox.currentItem()
        if not current_item:
            return
        k = current_item.text()
        try:
            current_cmds = {}
            if os.path.exists("command.json"):
                with open("command.json", "r", encoding="utf-8") as f:
                    current_cmds = json.load(f)
            if k in current_cmds:
                del current_cmds[k]
            with open("command.json", "w", encoding="utf-8") as f:
                json.dump(current_cmds, f, indent=2, ensure_ascii=False)
            
            refresh_sidebar_cb()
            log_cb(f"[SİSTEM] Komut silindi: {k}", "warn")
            dialog.accept()
        except Exception as e:
            log_cb(f"[HATA] Komut silinemedi: {str(e)}", "error")

    btn_del = QPushButton("Seçileni Sil")
    btn_del.setObjectName("danger")
    btn_del.clicked.connect(delete_cmd)
    layout.addWidget(btn_del)
    
    dialog.exec()

def show_desktop_image_analysis(parent, active_role_name, roles_dict, log_cb, update_last_response_cb):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Analiz Edilecek Görseli Seçin", "", "Görseller (*.png *.jpg *.jpeg *.webp *.gif)")
    if not file_path:
        return
        
    dialog = QDialog(parent)
    dialog.setWindowTitle("Görsel Analiz Sorusu")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(400, 180)
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Görsel hakkında ne sormak istersiniz?"))
    prompt_entry = QLineEdit()
    prompt_entry.setText("Bu fotoğrafta ne görüyorsun?")
    layout.addWidget(prompt_entry)
    
    def analyze():
        prompt = prompt_entry.text().strip()
        if not prompt:
            return
        dialog.accept()
        
        log_cb(f"[SİSTEM] Görsel analiz ediliyor ({os.path.basename(file_path)})...", "system")
        
        def do_analysis():
            try:
                with open(file_path, "rb") as img_f:
                    img_bytes = img_f.read()
                
                ext = os.path.splitext(file_path)[1].lower()
                mime = f"image/{ext[1:]}" if ext in (".png", ".webp", ".gif") else "image/jpeg"
                
                from search_bot import ask_gemini
                system_instruction = roles_dict.get(active_role_name, None)
                ans = ask_gemini(prompt, system_instruction=system_instruction, image_data={"mime_type": mime, "data": img_bytes})
                
                update_last_response_cb(ans)
                log_cb("\n[JARVIS - GÖRSEL ANALİZ]", "system")
                log_cb(ans)
                log_cb("")
            except Exception as e:
                log_cb(f"[HATA] Görsel analiz edilemedi: {str(e)}", "error")
                
        threading.Thread(target=do_analysis, daemon=True).start()

    btn_analiz = QPushButton("Analiz Et")
    btn_analiz.setObjectName("success")
    btn_analiz.clicked.connect(analyze)
    layout.addWidget(btn_analiz)
    
    dialog.exec()

def show_scheduled_reminder_popup(parent, rem_id, message, t_type, delete_cb):
    popup = QDialog(parent)
    popup.setWindowTitle("HATIRLATICI BİLDİRİMİ")
    popup.setStyleSheet(DIALOG_STYLE.replace(CYAN, AMBER))
    popup.setFixedSize(380, 200)
    popup.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    
    layout = QVBoxLayout(popup)
    
    title_lbl = QLabel(f"// {t_type.upper()} HATIRLATMA")
    title_lbl.setStyleSheet(f"color: {AMBER}; font-size: 14px;")
    title_lbl.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_lbl)
    
    msg_lbl = QLabel(message)
    msg_lbl.setWordWrap(True)
    msg_lbl.setStyleSheet("color: #ffffff; font-size: 13px;")
    msg_lbl.setAlignment(Qt.AlignCenter)
    layout.addWidget(msg_lbl)
    
    # Sound effect
    import winsound
    def play_sound():
        for _ in range(3):
            if not popup.isVisible():
                break
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            import time
            time.sleep(0.5)
    threading.Thread(target=play_sound, daemon=True).start()
    
    btn_layout = QHBoxLayout()
    btn_ok = QPushButton("TAMAM (KAPAT)")
    btn_ok.clicked.connect(popup.accept)
    btn_layout.addWidget(btn_ok)
    
    btn_del = QPushButton("HATIRLATICIYI SİL")
    btn_del.setObjectName("danger")
    def on_delete():
        delete_cb(rem_id)
        popup.accept()
    btn_del.clicked.connect(on_delete)
    btn_layout.addWidget(btn_del)
    
    layout.addLayout(btn_layout)
    popup.exec()

def show_reminder_manager_dialog(parent, log_cb):
    import scheduler
    dialog = QDialog(parent)
    dialog.setWindowTitle("Hatırlatıcı Yönetimi")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(600, 480)
    
    layout = QHBoxLayout(dialog)
    
    # Left container
    left_layout = QVBoxLayout()
    left_layout.addWidget(QLabel("// AKTİF HATIRLATICILAR"))
    
    listbox = QListWidget()
    left_layout.addWidget(listbox)
    
    rem_ids_in_list = []
    
    def populate_listbox():
        listbox.clear()
        rem_ids_in_list.clear()
        reminders = scheduler.load_reminders()
        for rem_id, rem in reminders.items():
            rem_ids_in_list.append(rem_id)
            if rem["type"] == "recurrent":
                info = f"[Tekrarlı] {rem['message']} (Her {rem['interval_minutes']} dk)"
            else:
                freq_info = f" (Sıklık: {rem['frequency_minutes']} dk)" if rem.get('frequency_minutes', 0) > 0 else ""
                info = f"[Zamanlı] {rem['message']} ({rem['target_time']}{freq_info})"
            listbox.addItem(info)
            
    populate_listbox()
    
    def delete_selected():
        row = listbox.currentRow()
        if row < 0:
            return
        rem_id = rem_ids_in_list[row]
        if scheduler.delete_reminder(rem_id):
            log_cb(f"[SİSTEM] Hatırlatıcı silindi (ID: {rem_id})", "system")
            populate_listbox()
            
    btn_del = QPushButton("SEÇİLENİ SİL")
    btn_del.setObjectName("danger")
    btn_del.clicked.connect(delete_selected)
    left_layout.addWidget(btn_del)
    
    # Right container
    right_layout = QVBoxLayout()
    right_layout.addWidget(QLabel("// YENİ HATIRLATICI"))
    
    type_group = QButtonGroup(dialog)
    btn_rec = QRadioButton("Tekrarlı")
    btn_once = QRadioButton("Zamanlanmış")
    btn_rec.setChecked(True)
    type_group.addButton(btn_rec)
    type_group.addButton(btn_once)
    
    radio_layout = QHBoxLayout()
    radio_layout.addWidget(btn_rec)
    radio_layout.addWidget(btn_once)
    right_layout.addLayout(radio_layout)
    
    inputs_container = QVBoxLayout()
    right_layout.addLayout(inputs_container)
    
    inputs_widgets = []
    
    def draw_inputs():
        for w in inputs_widgets:
            inputs_container.removeWidget(w)
            w.deleteLater()
        inputs_widgets.clear()
        
        lbl_msg = QLabel("Hatırlatma Mesajı")
        msg_entry = QLineEdit()
        inputs_container.addWidget(lbl_msg)
        inputs_container.addWidget(msg_entry)
        inputs_widgets.extend([lbl_msg, msg_entry])
        
        if btn_rec.isChecked():
            lbl_val = QLabel("Tekrarlama Aralığı (Dakika)")
            val_entry = QLineEdit()
            val_entry.setText("30")
            inputs_container.addWidget(lbl_val)
            inputs_container.addWidget(val_entry)
            inputs_widgets.extend([lbl_val, val_entry])
            
            def add_rec():
                msg = msg_entry.text().strip()
                val = val_entry.text().strip()
                if not msg or not val:
                    return
                try:
                    mins = float(val)
                except ValueError:
                    return
                scheduler.add_recurrent_reminder(msg, mins)
                log_cb(f"[SİSTEM] Yeni tekrarlı hatırlatıcı kuruldu (Her {mins} dk): '{msg}'", "system")
                populate_listbox()
                msg_entry.clear()
                
            btn_add = QPushButton("EKLE (TEKRARLI)")
            btn_add.setObjectName("success")
            btn_add.clicked.connect(add_rec)
            inputs_container.addWidget(btn_add)
            inputs_widgets.append(btn_add)
            
        else:
            lbl_time = QLabel("Tarih & Saat (Örn: 22.06.2026 14:00)")
            time_entry = QLineEdit()
            from datetime import datetime, timedelta
            suggested = (datetime.now() + timedelta(minutes=30)).strftime("%d.%m.%Y %H:%M")
            time_entry.setText(suggested)
            inputs_container.addWidget(lbl_time)
            inputs_container.addWidget(time_entry)
            inputs_widgets.extend([lbl_time, time_entry])
            
            lbl_freq = QLabel("Bildirim Sıklığı (Dakika, 0 = Tek Sefer)")
            freq_entry = QLineEdit()
            freq_entry.setText("15")
            inputs_container.addWidget(lbl_freq)
            inputs_container.addWidget(freq_entry)
            inputs_widgets.extend([lbl_freq, freq_entry])
            
            def add_once():
                msg = msg_entry.text().strip()
                t_str = time_entry.text().strip()
                freq = freq_entry.text().strip()
                if not msg or not t_str:
                    return
                try:
                    f_val = float(freq) if freq else 0.0
                except ValueError:
                    return
                try:
                    scheduler.add_once_reminder(msg, t_str, f_val)
                    log_cb(f"[SİSTEM] Yeni zamanlanmış hatırlatıcı kuruldu ({t_str}): '{msg}'", "system")
                    populate_listbox()
                    msg_entry.clear()
                except Exception as e:
                    log_cb(f"[HATA] Hatırlatıcı kurulamadı: {str(e)}", "error")
                    
            btn_add = QPushButton("EKLE (ZAMANLI)")
            btn_add.setObjectName("success")
            btn_add.clicked.connect(add_once)
            inputs_container.addWidget(btn_add)
            inputs_widgets.append(btn_add)
            
    btn_rec.toggled.connect(draw_inputs)
    draw_inputs()
    
    layout.addLayout(left_layout)
    layout.addLayout(right_layout)
    
    dialog.exec()

def show_telegram_settings_dialog(parent, log_cb):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Telegram Bot Ayarları")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(420, 340)
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("// TELEGRAM BOT AYARLARI"))
    
    from dotenv import load_dotenv
    load_dotenv()
    token_val = os.getenv("TELEGRAM_BOT_TOKEN", "")
    allowed_val = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
    pin_val = os.getenv("TELEGRAM_AUTH_PIN", "123456")
    
    layout.addWidget(QLabel("Telegram Bot Token"))
    token_entry = QLineEdit()
    token_entry.setText(token_val)
    layout.addWidget(token_entry)
    
    layout.addWidget(QLabel("İzinli Kullanıcı ID'leri (virgülle ayırın)"))
    allowed_entry = QLineEdit()
    allowed_entry.setText(allowed_val)
    layout.addWidget(allowed_entry)
    
    layout.addWidget(QLabel("Giriş / Yetkilendirme Şifresi (PIN)"))
    pin_entry = QLineEdit()
    pin_entry.setText(pin_val)
    layout.addWidget(pin_entry)
    
    def on_save():
        new_token = token_entry.text().strip()
        new_allowed = allowed_entry.text().strip()
        new_pin = pin_entry.text().strip()
        
        if not new_pin:
            return
            
        try:
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    env_lines = f.readlines()
                    
            def set_env_var(key, val):
                found = False
                for idx, line in enumerate(env_lines):
                    if line.strip().startswith(f"{key}="):
                        env_lines[idx] = f"{key}={val}\n"
                        found = True
                        break
                if not found:
                    env_lines.append(f"{key}={val}\n")
                    
            set_env_var("TELEGRAM_BOT_TOKEN", new_token)
            set_env_var("TELEGRAM_ALLOWED_USER_IDS", new_allowed)
            set_env_var("TELEGRAM_AUTH_PIN", new_pin)
            
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(env_lines)
                
            log_cb("[TELEGRAM] Ayarlar güncellendi. Şifre ve İzinli ID'ler anında güncellendi (Token değişikliği için uygulamayı yeniden başlatın).", "system")
            dialog.accept()
        except Exception as e:
            log_cb(f"[HATA] Ayarlar kaydedilemedi: {str(e)}", "error")

    btn_save = QPushButton("KAYDET")
    btn_save.setObjectName("success")
    btn_save.clicked.connect(on_save)
    layout.addWidget(btn_save)
    
    dialog.exec()

def show_welcome_guide(parent):
    import webbrowser
    dialog = QDialog(parent)
    dialog.setWindowTitle("NexusHUD Kurulum ve Kullanım Kılavuzu")
    dialog.setStyleSheet(DIALOG_STYLE)
    dialog.setFixedSize(580, 500)
    
    layout = QVBoxLayout(dialog)
    
    lbl_title = QLabel("// NEXUSHUD HOŞ GELDİNİZ")
    lbl_title.setStyleSheet(f"color: {CYAN}; font-size: 16px; font-weight: bold;")
    lbl_title.setAlignment(Qt.AlignCenter)
    layout.addWidget(lbl_title)
    
    guide_text = (
        "NexusHUD'ı kullanmaya başlamak için gerekli API anahtarlarını tanımlamanız gerekmektedir.\n\n"
        "1️⃣ **Google Gemini API Anahtarı:**\n"
        "• Yapay zeka ile sohbet ve görsel analiz özellikleri için gereklidir.\n"
        "• Google AI Studio adresine gidip ücretsiz anahtar oluşturabilirsiniz.\n\n"
        "2️⃣ **Telegram Bot Token:**\n"
        "• Bilgisayarınızı uzaktan kontrol etmek ve bildirim almak için gereklidir.\n"
        "• Telegram'da BotFather'a gidip '/newbot' komutu ile bot oluşturabilirsiniz."
    )
    
    lbl_desc = QLabel(guide_text)
    lbl_desc.setWordWrap(True)
    lbl_desc.setStyleSheet("color: #ffffff; font-size: 12px; line-height: 18px;")
    layout.addWidget(lbl_desc)
    
    # Buttons for links
    btn_layout = QHBoxLayout()
    
    btn_gemini_link = QPushButton("🔑 Gemini API Anahtarı Al")
    btn_gemini_link.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/"))
    btn_layout.addWidget(btn_gemini_link)
    
    btn_tg_link = QPushButton("🤖 Telegram BotFather Git")
    btn_tg_link.clicked.connect(lambda: webbrowser.open("https://t.me/BotFather"))
    btn_layout.addWidget(btn_tg_link)
    
    layout.addLayout(btn_layout)
    
    lbl_pin_info = QLabel(
        "3️⃣ **Başlatma ve Kimlik Doğrulama:**\n"
        "• Anahtarlarınızı kaydettikten sonra botu çalıştırın.\n"
        "• Telegram üzerinden botunuza ilk mesajı gönderdiğinizde bot kilitli olacaktır.\n"
        "• Arayüzde veya '.env' dosyasında yazan **Giriş Şifresini (PIN)** bota göndererek kendinizi yetkilendirin.\n"
        "• Varsayılan şifre: **123456**"
    )
    lbl_pin_info.setWordWrap(True)
    lbl_pin_info.setStyleSheet(f"color: {AMBER}; font-size: 12px;")
    layout.addWidget(lbl_pin_info)
    
    btn_close = QPushButton("KURULUMA BAŞLA")
    btn_close.setObjectName("success")
    btn_close.clicked.connect(dialog.accept)
    layout.addWidget(btn_close)
    
    dialog.exec()

