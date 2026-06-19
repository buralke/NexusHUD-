import time
import os
import requests
import threading
import random
import json
import subprocess
import system_utils

# Global Cache to bypass Telegram's 64-byte callback_data limit
path_cache = {}
path_counter = 0

def cache_path(abs_path):
    global path_counter
    abs_path = os.path.abspath(abs_path)
    for k, v in path_cache.items():
        if v == abs_path:
            return k
    path_counter += 1
    key = f"p{path_counter}"
    path_cache[key] = abs_path
    return key

def get_ls_markup(target_dir):
    try:
        target_dir = os.path.abspath(target_dir)
        items = os.listdir(target_dir)
        dirs = []
        files = []
        for item in items:
            full_p = os.path.join(target_dir, item)
            if os.path.isdir(full_p):
                dirs.append(item)
            else:
                files.append(item)
        
        dirs.sort()
        files.sort()
        
        inline_keyboard = {"inline_keyboard": []}
        
        # Parent directory button
        parent = os.path.dirname(target_dir)
        if parent and parent != target_dir:
            p_key = cache_path(parent)
            inline_keyboard["inline_keyboard"].append([
                {"text": "⬆ Üst Klasör", "callback_data": f"ls:{p_key}"}
            ])
            
        # Add subfolders (limit to 12 items to prevent long keyboards)
        for d in dirs[:12]:
            full_p = os.path.join(target_dir, d)
            d_key = cache_path(full_p)
            inline_keyboard["inline_keyboard"].append([
                {"text": f"📁 {d}", "callback_data": f"ls:{d_key}"}
            ])
            
        # Add files (limit to 12 items)
        for f in files[:12]:
            full_p = os.path.join(target_dir, f)
            f_key = cache_path(full_p)
            inline_keyboard["inline_keyboard"].append([
                {"text": f"📄 {f}", "callback_data": f"dl:{f_key}"}
            ])
            
        total_shown = len(dirs[:12]) + len(files[:12])
        total_items = len(dirs) + len(files)
        info_text = f"📂 *Dizin:* `{target_dir}`\n\nGösterilen: {total_shown} / {total_items} öge."
        
        return info_text, inline_keyboard
    except Exception as e:
        return f"❌ Klasör okunamadı: {str(e)}", None

def start_telegram_bot(token, allowed_ids_str, log_cb, run_cmd_cb, roles_dict, role_var, update_last_response_cb, add_reminder_cb, set_role_cb):
    if not token or not token.strip():
        log_cb("[TELEGRAM] Token bulunamadı. Telegram Bot başlatılmadı.", "warn")
        return

    def load_telegram_config():
        from dotenv import load_dotenv
        import importlib
        import dotenv
        importlib.reload(dotenv)
        dotenv.load_dotenv(override=True)
        
        current_pin = os.getenv("TELEGRAM_AUTH_PIN", "123456").strip()
        if not current_pin:
            current_pin = "123456"
            
        current_ids = []
        ids_str = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
        if ids_str:
            for val in ids_str.split(","):
                val = val.strip()
                if val.isdigit():
                    current_ids.append(int(val))
        return current_ids, current_pin

    init_allowed_ids, init_auth_pin = load_telegram_config()

    def bot_loop():
        if not init_allowed_ids:
            log_cb("[TELEGRAM GÜVENLİK] Herhangi bir yetkili ID tanımlanmamış.", "warn")
            log_cb(f"[TELEGRAM GÜVENLİK] Yetkilendirme şifresi (Auth PIN): {init_auth_pin}", "warn")
        else:
            log_cb(f"[TELEGRAM] Bot başlatılıyor (İzinli ID'ler: {init_allowed_ids})...", "system")
        
        # Register commands for the autocomplete menu
        set_commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
        commands_payload = {
            "commands": [
                {"command": "stats", "description": "Sistem Durumu (CPU & RAM)"},
                {"command": "screen", "description": "Ekran Görüntüsü Al"},
                {"command": "cam", "description": "Kameradan Fotoğraf Çek"},
                {"command": "notifications", "description": "Son Bildirimleri Oku"},
                {"command": "clip", "description": "Pano İçeriğini Oku"},
                {"command": "roles", "description": "AI Rollerini Listele"},
                {"command": "reminders", "description": "Aktif Hatırlatıcıları Yönet"},
                {"command": "shutdown", "description": "Bilgisayarı Kapat"},
                {"command": "restart", "description": "Bilgisayarı Yeniden Başlat"},
                {"command": "help", "description": "Tüm Komutları Göster"}
            ]
        }
        try:
            requests.post(set_commands_url, json=commands_payload, timeout=10)
        except Exception as e:
            log_cb(f"[TELEGRAM UYARI] Komut menüsü kaydedilemedi: {str(e)}", "warn")

        offset = 0
        get_updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
        send_msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        send_photo_url = f"https://api.telegram.org/bot{token}/sendPhoto"
        send_doc_url = f"https://api.telegram.org/bot{token}/sendDocument"
        get_file_url = f"https://api.telegram.org/bot{token}/getFile"
        answer_cb_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        edit_msg_url = f"https://api.telegram.org/bot{token}/editMessageText"
        file_download_prefix = f"https://api.telegram.org/file/bot{token}/"

        # Custom permanent Reply Keyboard menu
        main_keyboard = {
            "keyboard": [
                [{"text": "📊 Sistem Durumu"}, {"text": "📸 Ekran Görüntüsü"}],
                [{"text": "📷 Kamera Çekimi"}, {"text": "🔔 Bildirimler"}],
                [{"text": "📋 Panoyu Oku"}, {"text": "🎭 AI Rolleri"}],
                [{"text": "❓ Yardım/Komutlar"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

        while True:
            try:
                params = {"offset": offset, "timeout": 30}
                res = requests.get(get_updates_url, params=params, timeout=35)
                if res.status_code != 200:
                    time.sleep(5)
                    continue

                data = res.json()
                if not data.get("ok"):
                    time.sleep(5)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    # Handle Callback Queries (from Inline Buttons)
                    cb_query = update.get("callback_query")
                    if cb_query:
                        cb_id = cb_query.get("id")
                        cb_data = cb_query.get("data")
                        cb_message = cb_query.get("message", {})
                        cb_chat_id = cb_message.get("chat", {}).get("id")
                        cb_user_id = cb_query.get("from", {}).get("id")
                        cb_username = cb_query.get("from", {}).get("username", "Bilinmeyen")
                        
                        # Security Verification
                        allowed_ids, auth_pin = load_telegram_config()
                        if cb_user_id not in allowed_ids:
                            log_cb(f"[TELEGRAM GÜVENLİK] Yetkisiz buton tıklaması: {cb_username} (ID: {cb_user_id})", "error")
                            requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "🚫 Yetkiniz bulunmamaktadır. Lütfen önce bota şifre göndererek yetki almalısınız."})
                            continue
                            
                        # Callback: Set Role
                        if cb_data.startswith("setrole:"):
                            role_to_set = cb_data.split(":", 1)[1]
                            if role_to_set in roles_dict:
                                set_role_cb(role_to_set)
                                log_cb(f"[TELEGRAM] Yapay zeka rolü değiştirildi: {role_to_set}", "system")
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": f"Rol {role_to_set} olarak ayarlandı."})
                                requests.post(send_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "text": f"👤 Yapay zeka aktif rolü *{role_to_set}* olarak güncellendi.",
                                    "parse_mode": "Markdown"
                                })
                            else:
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Rol bulunamadı."})
                            continue

                        # Callback: Run Shortcut
                        if cb_data.startswith("runshortcut:"):
                            shortcut_key = cb_data.split(":", 1)[1]
                            run_cmd_cb(shortcut_key)
                            log_cb(f"[TELEGRAM] Kısayol çalıştırıldı: {shortcut_key}", "system")
                            requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": f"🚀 {shortcut_key} başlatıldı."})
                            continue

                        # Callback: File List Navigation
                        if cb_data.startswith("ls:"):
                            dir_key = cb_data.split(":", 1)[1]
                            target_dir = path_cache.get(dir_key)
                            if target_dir and os.path.exists(target_dir) and os.path.isdir(target_dir):
                                info_text, markup = get_ls_markup(target_dir)
                                requests.post(edit_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "message_id": cb_message.get("message_id"),
                                    "text": info_text,
                                    "parse_mode": "Markdown",
                                    "reply_markup": markup
                                })
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Klasör güncellendi."})
                            else:
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Klasör bulunamadı."})
                            continue

                        # Callback: File Download
                        if cb_data.startswith("dl:"):
                            file_key = cb_data.split(":", 1)[1]
                            target_file = path_cache.get(file_key)
                            if target_file and os.path.exists(target_file) and os.path.isfile(target_file):
                                log_cb(f"[TELEGRAM] {cb_username} dosya indirme talebinde bulundu: {target_file}", "system")
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Dosya gönderiliyor..."})
                                try:
                                    with open(target_file, "rb") as f:
                                        requests.post(send_doc_url, data={"chat_id": cb_chat_id}, files={"document": f})
                                except Exception as e:
                                    requests.post(send_msg_url, json={"chat_id": cb_chat_id, "text": f"❌ Dosya gönderilemedi: {str(e)}"})
                            else:
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Dosya bulunamadı."})
                            continue

                        # Callback: Delete Reminder
                        if cb_data.startswith("delrem:"):
                            rem_id = cb_data.split(":", 1)[1]
                            import scheduler
                            if scheduler.delete_reminder(rem_id):
                                log_cb(f"[TELEGRAM] Hatırlatıcı uzaktan kapatıldı/silindi (ID: {rem_id})", "system")
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "✅ Hatırlatıcı silindi."})
                                # Edit the message to show it is dismissed
                                requests.post(edit_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "message_id": cb_message.get("message_id"),
                                    "text": f"🔔 ~{cb_message.get('text', '')}~\n\n❌ *Hatırlatıcı Kapatıldı.*",
                                    "parse_mode": "Markdown"
                                })
                            else:
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "❌ Hatırlatıcı bulunamadı veya zaten silinmiş."})
                            continue

                        # Callback: Power Controls
                        if cb_data.startswith("power:"):
                            action = cb_data.split(":", 1)[1]
                            if action == "shutdown_confirm":
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Bilgisayar kapatılıyor..."})
                                requests.post(edit_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "message_id": cb_message.get("message_id"),
                                    "text": "🔌 *Bilgisayar 5 saniye içinde kapatılıyor...*"
                                })
                                log_cb("[TELEGRAM] Uzaktan kapatma komutu verildi.", "warn")
                                subprocess.Popen("shutdown /s /t 5", shell=True)
                            elif action == "restart_confirm":
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "Bilgisayar yeniden başlatılıyor..."})
                                requests.post(edit_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "message_id": cb_message.get("message_id"),
                                    "text": "🔄 *Bilgisayar 5 saniye içinde yeniden başlatılıyor...*"
                                })
                                log_cb("[TELEGRAM] Uzaktan yeniden başlatma komutu verildi.", "warn")
                                subprocess.Popen("shutdown /r /t 5", shell=True)
                            elif action == "cancel":
                                requests.post(answer_cb_url, json={"callback_query_id": cb_id, "text": "İşlem iptal edildi."})
                                requests.post(edit_msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "message_id": cb_message.get("message_id"),
                                    "text": "❌ *Güç işlemi iptal edildi.*"
                                })
                            continue
                        continue

                    message = update.get("message")
                    if not message:
                        continue

                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    from_user = message.get("from", {})
                    user_id = from_user.get("id")
                    username = from_user.get("username", "Bilinmeyen")

                    # Security Verification
                    allowed_ids, auth_pin = load_telegram_config()
                    if user_id not in allowed_ids:
                        text_val = message.get("text", "").strip()
                        if text_val == auth_pin:
                            try:
                                env_lines = []
                                if os.path.exists(".env"):
                                    with open(".env", "r", encoding="utf-8") as f:
                                        env_lines = f.readlines()
                                found_ids_line = False
                                for idx, line in enumerate(env_lines):
                                    if line.strip().startswith("TELEGRAM_ALLOWED_USER_IDS="):
                                        current_val = line.split("=", 1)[1].strip()
                                        if current_val:
                                            existing_ids = [x.strip() for x in current_val.split(",") if x.strip()]
                                            if str(user_id) not in existing_ids:
                                                existing_ids.append(str(user_id))
                                            new_val = ",".join(existing_ids)
                                        else:
                                            new_val = str(user_id)
                                        env_lines[idx] = f"TELEGRAM_ALLOWED_USER_IDS={new_val}\n"
                                        found_ids_line = True
                                        break
                                if not found_ids_line:
                                    env_lines.append(f"TELEGRAM_ALLOWED_USER_IDS={user_id}\n")
                                with open(".env", "w", encoding="utf-8") as f:
                                    f.writelines(env_lines)
                                
                                log_cb(f"[SİSTEM] {username} (ID: {user_id}) Telegram botu için yetkilendirildi ve .env dosyasına kaydedildi.", "system")
                                requests.post(send_msg_url, json={
                                    "chat_id": chat_id,
                                    "text": f"✅ Tebrikler! Yetkilendirme başarılı.\n\n👤 Kullanıcı: {username}\n🆔 ID: {user_id}\n\nArtık botu kullanabilirsiniz. Komut listesi için `/help` yazabilirsiniz."
                                })
                            except Exception as e:
                                log_cb(f"[HATA] Yetki kaydedilemedi: {str(e)}", "error")
                                requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Yetki kaydedilemedi: {str(e)}"})
                        else:
                            log_cb(f"[TELEGRAM GÜVENLİK] Yetkisiz erişim denemesi: {username} (ID: {user_id})", "error")
                            requests.post(send_msg_url, json={
                                "chat_id": chat_id,
                                "text": "🔒 *Güvenlik Kilidi Aktif!*\n\nLütfen bilgisayarınızın kontrol panelinde veya .env dosyasında belirlenmiş olan yetkilendirme şifresini gönderin.",
                                "parse_mode": "Markdown"
                            })
                        continue

                    # Process Documents (File Upload to PC)
                    doc = message.get("document")
                    if doc:
                        file_name = doc.get("file_name", "uploaded_file")
                        file_id = doc.get("file_id")
                        log_cb(f"[TELEGRAM] {username} bir dosya gönderdi: {file_name}. Bilgisayara kaydediliyor...", "system")
                        
                        try:
                            file_info_res = requests.get(get_file_url, params={"file_id": file_id})
                            file_path = file_info_res.json()["result"]["file_path"]
                            file_bytes = requests.get(file_download_prefix + file_path).content
                            
                            out_path = os.path.join(os.getcwd(), file_name)
                            with open(out_path, "wb") as out_f:
                                out_f.write(file_bytes)
                                
                            log_cb(f"[TELEGRAM] Dosya başarıyla kaydedildi: {out_path}", "system")
                            requests.post(send_msg_url, json={
                                "chat_id": chat_id,
                                "text": f"📥 Dosya bilgisayara başarıyla kaydedildi:\n`{out_path}`",
                                "parse_mode": "Markdown"
                            })
                        except Exception as e:
                            log_cb(f"[TELEGRAM HATA] Dosya kaydedilemedi: {str(e)}", "error")
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Dosya kaydedilemedi: {str(e)}"})
                        continue

                    # Process Photo (Gemini Multimodal Analysis)
                    photo = message.get("photo")
                    caption = message.get("caption", "Bu fotoğrafta ne görüyorsun?").strip()
                    
                    if photo:
                        log_cb(f"[TELEGRAM] {username} bir görsel gönderdi. Analiz ediliyor...", "system")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": "📷 Görseliniz alındı, Gemini analiz ediyor..."})
                        
                        try:
                            largest_photo = photo[-1]
                            file_id = largest_photo["file_id"]
                            
                            file_info_res = requests.get(get_file_url, params={"file_id": file_id})
                            file_path = file_info_res.json()["result"]["file_path"]
                            
                            file_bytes = requests.get(file_download_prefix + file_path).content
                            
                            ext = os.path.splitext(file_path)[1].lower()
                            mime_type = "image/jpeg"
                            if ext in (".png", ".webp", ".gif"):
                                mime_type = f"image/{ext[1:]}"
                                
                            from search_bot import ask_gemini
                            active_role = role_var.get()
                            system_instruction = roles_dict.get(active_role, None)
                            ans = ask_gemini(caption, system_instruction=system_instruction, image_data={"mime_type": mime_type, "data": file_bytes})
                            
                            update_last_response_cb(ans)
                            log_cb(f"\n[JARVIS - Telegram Görsel Analiz]\n{ans}\n", "system")
                            
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🤖 Gemini Yanıtı:\n\n{ans}"})
                        except Exception as e:
                            log_cb(f"[TELEGRAM HATA] Görsel analiz edilemedi: {str(e)}", "error")
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Görsel analiz edilemedi: {str(e)}"})
                        continue

                    # Process Text
                    text = message.get("text", "").strip()
                    if not text:
                        continue

                    text_lower = text.lower()

                    # Map custom reply keyboard buttons to standard commands
                    reply_map = {
                        "📊 sistem durumu": "/stats",
                        "📸 ekran görüntüsü": "/screen",
                        "📷 kamera çekimi": "/cam",
                        "🔔 bildirimler": "/notifications",
                        "📋 panoyu oku": "/clip",
                        "🎭 ai rolleri": "/roles",
                        "❓ yardım/komutlar": "/help"
                    }
                    if text_lower in reply_map:
                        text_lower = reply_map[text_lower]

                    # /start Command (Shortcut Grid Menu)
                    if text_lower == "/start":
                        try:
                            with open("command.json", "r", encoding="utf-8") as f:
                                cmds_temp = json.load(f)
                            shortcut_keys = list(cmds_temp.keys())
                        except Exception:
                            shortcut_keys = []

                        inline_keyboard = {"inline_keyboard": []}
                        row = []
                        for k in shortcut_keys:
                            row.append({"text": f"🚀 {k.upper()}", "callback_data": f"runshortcut:{k}"})
                            if len(row) == 2:
                                inline_keyboard["inline_keyboard"].append(row)
                                row = []
                        if row:
                            inline_keyboard["inline_keyboard"].append(row)

                        welcome_text = (
                            "👋 *NexusHUD Kontrol Paneline Hoş Geldiniz!*\n\n"
                            "Aşağıdaki butonlara tıklayarak bilgisayarınızdaki kısayolları anında başlatabilirsiniz:\n\n"
                            "ℹ️ *Diğer Komutlar:* Klavyenin altındaki menüyü veya `/help` komutunu kullanabilirsiniz."
                        )
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id,
                            "text": welcome_text,
                            "parse_mode": "Markdown",
                            "reply_markup": inline_keyboard
                        })
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id,
                            "text": "📱 Hızlı kontrol tuşları klavyenizin altına eklendi. `/help` yazarak detaylı kılavuzu görebilirsiniz.",
                            "reply_markup": main_keyboard
                        })
                        continue

                    # /help or other helper Commands
                    if text_lower in ("/help", "yardim", "help", "/commands"):
                        try:
                            with open("command.json", "r", encoding="utf-8") as f:
                                cmds_temp = json.load(f)
                            shortcuts_list = [f"`{k}`" for k in cmds_temp.keys()]
                        except Exception:
                            shortcuts_list = []
                        shortcuts_str = ", ".join(shortcuts_list) if shortcuts_list else "(Kayıtlı kısayol yok)"

                        roles_list = [f"`{r}`" for r in roles_dict.keys()]
                        roles_str = ", ".join(roles_list) if roles_list else "`Jarvis`"

                        help_text = (
                            "👋 *NexusHUD Telegram Kontrol Paneline Hoş Geldiniz!*\n\n"
                            "💻 *Sistem Durumu & Donanım:*\n"
                            "📊 `/stats` - CPU & RAM kullanım oranları\n"
                            "🔆 `/brightness <0-100>` - Ekran parlaklığını ayarlar\n"
                            "🔋 `/power <balanced/high/saver>` - Güç planını ayarlar\n"
                            "🔊 `/say <metin>` - Bilgisayar hoparlöründen seslendirir\n\n"
                            "📷 *Kamera & Ekran Görüntüsü:*\n"
                            "📸 `/screen` - Ekran görüntüsü alır\n"
                            "📷 `/cam` - PC kamerasından fotoğraf çekip gönderir\n\n"
                            "📋 *Pano İşlemleri (Clipboard):*\n"
                            "📋 `/clip` - Bilgisayar panosundaki metni okur\n"
                            "✍️ `/setclip <metin>` - Bilgisayar panosuna metin yazar\n\n"
                            "⏰ *Zamanlayıcı / Hatırlatıcı:*\n"
                            "⏰ `/rem <dakika> <mesaj>` - Bilgisayara zamanlayıcı uyarısı kurar\n\n"
                            "🎭 *Yapay Zeka Rol Yönetimi:*\n"
                            "🎭 `/roles` - Mevcut yapay zeka rollerini listeler (Tıklanabilir Butonlar)\n"
                            "👤 `/setrole <rol_adı>` - Aktif yapay zeka rolünü değiştirir\n"
                            "👉 *Aktif Roller:* " + roles_str + "\n\n"
                            "🎵 *Müzik Arama:*\n"
                            "🎵 `/spotify <arama_terimi>` - Bilgisayarda Spotify araması açar\n\n"
                            "📂 *Dosya Yönetimi (Dokunmatik Gezgin):*\n"
                            "📁 `/ls [klasör_yolu]` - Dosya ve klasörleri buton olarak listeler\n"
                            "📤 `/download <dosya_yolu>` - Bilgisayardan dosya indirir\n"
                            "📥 *Dosya Gönderimi:* Bota direkt dosya yollayarak bilgisayara kaydedebilirsiniz.\n\n"
                            "🛠 *Shell & Süreç Yönetimi:*\n"
                            "💻 `/cmd <komut>` - Windows CMD üzerinde komut çalıştırır\n"
                            "📋 `/ps` - Çalışan süreçleri listeler\n"
                            "❌ `/kill <program_adi.exe>` - Çalışan programı kapatır\n\n"
                            "🔌 *Güç Kontrolleri (Güvenli Onaylı):*\n"
                            "🔌 `/shutdown` - Bilgisayarı kapat (Onaylı)\n"
                            "🔄 `/restart` - Bilgisayarı yeniden başlat (Onaylı)\n"
                            "🔒 `/lock` - Kilitle | 💤 `/sleep` - Uyut\n"
                            "🔇 `/mute` - Sessiz | ⏯ `/play` - Oynat/Durdur\n"
                            "🔊 `/volup` - Ses + | 🔉 `/voldown` - Ses -\n"
                            "🔔 `/notifications` - Son gelen Windows bildirimlerini okur\n\n"
                            "⚡️ *Kayıtlı Kısayol Kelimeleriniz (command.json):*\n"
                            "👉 " + shortcuts_str + "\n\n"
                            "🔍 *Arama ve Chat:* `bul <konu>` araması yapabilir ya da direkt mesaj atarak Gemini ile sohbet edebilirsiniz."
                        )
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id, 
                            "text": help_text, 
                            "parse_mode": "Markdown",
                            "reply_markup": main_keyboard
                        })
                        continue

                    # Notifications Command
                    if text_lower in ("/notifications", "/alerts", "/bildirimler"):
                        log_cb(f"[TELEGRAM] {username} bildirimleri talep etti.", "system")
                        try:
                            notifications = system_utils.get_windows_notifications(10)
                            if not notifications:
                                resp_text = "📭 Aktif bildirim bulunamadı."
                            else:
                                list_items = []
                                for idx, n in enumerate(notifications, 1):
                                    list_items.append(f"{idx}. *{n['app']}* ({n['time']}):\n{n['content']}")
                                resp_text = "🔔 *Windows Bildirimleri:*\n\n" + "\n\n".join(list_items)
                        except Exception as e:
                            resp_text = f"❌ Bildirimler alınırken hata oluştu: {str(e)}"
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp_text, "parse_mode": "Markdown"})
                        continue

                    # Stats Command
                    if text_lower == "/stats":
                        cpu = system_utils.get_cpu_usage()
                        ram = system_utils.get_ram_usage()
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id,
                            "text": f"📊 *Sistem Metrikleri:*\n🖥 *CPU Yükü:* {cpu}%\n🧠 *RAM Kullanımı:* {ram}%",
                            "parse_mode": "Markdown"
                        })
                        continue

                    # Clipboard Get Command (/clip)
                    if text_lower == "/clip":
                        text_val = system_utils.get_clipboard_text()
                        if not text_val.strip():
                            resp = "📋 Bilgisayar panosu boş."
                        else:
                            resp = f"📋 *Pano İçeriği:*\n`{text_val}`"
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Clipboard Set Command (/setclip)
                    if text_lower.startswith("/setclip "):
                        clip_val = text.split(" ", 1)[1].strip()
                        if system_utils.set_clipboard_text(clip_val):
                            log_cb(f"[TELEGRAM] Pano içeriği uzaktan güncellendi.", "system")
                            resp = "✅ Metin bilgisayar panosuna başarıyla kopyalandı."
                        else:
                            resp = "❌ Pano güncellenemedi."
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp})
                        continue

                    # Reminders List Command (/reminders)
                    if text_lower in ("/reminders", "/hatirlaticilar"):
                        import scheduler
                        reminders = scheduler.load_reminders()
                        if not reminders:
                            resp = "⏰ Aktif hatırlatıcı bulunamadı."
                        else:
                            lines = ["⏰ *Aktif Hatırlatıcılar:*"]
                            for r_id, r in reminders.items():
                                if r["type"] == "recurrent":
                                    lines.append(f"• *[Tekrarlı]* `{r_id}`: {r['message']} (Her {r['interval_minutes']} dk)")
                                else:
                                    freq_info = f" (Sıklık: {r['frequency_minutes']} dk)" if r.get('frequency_minutes', 0) > 0 else ""
                                    lines.append(f"• *[Zamanlı]* `{r_id}`: {r['message']} ({r['target_time']}{freq_info})")
                            lines.append("\nSilmek için: `/remdelete <id>`")
                            resp = "\n".join(lines)
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Reminder Delete Command (/remdelete)
                    if text_lower.startswith("/remdelete ") or text_lower.startswith("/remsil "):
                        parts = text.split(" ", 1)
                        r_id = parts[1].strip()
                        import scheduler
                        if scheduler.delete_reminder(r_id):
                            resp = f"✅ Hatırlatıcı başarıyla silindi: `{r_id}`"
                        else:
                            resp = f"❌ Hatırlatıcı bulunamadı: `{r_id}`"
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Reminder Command (/rem)
                    if text_lower.startswith("/rem "):
                        parts = text.split(" ")
                        if len(parts) >= 4:
                            mode = parts[1].lower()
                            import scheduler
                            if mode in ("recurrent", "tekrar"):
                                try:
                                    mins = float(parts[2])
                                    msg = " ".join(parts[3:])
                                    r_id = scheduler.add_recurrent_reminder(msg, mins)
                                    resp = f"⏰ Tekrarlı hatırlatıcı kuruldu (ID: `{r_id}`):\nHer {mins} dakikada bir '{msg}'"
                                except Exception as e:
                                    resp = f"❌ Hata: {str(e)}"
                            elif mode in ("once", "zamanli", "birkez"):
                                if len(parts) >= 6:
                                    date_str = parts[2]
                                    time_str = parts[3]
                                    target_dt_str = f"{date_str} {time_str}"
                                    try:
                                        freq = float(parts[4])
                                        msg = " ".join(parts[5:])
                                        r_id = scheduler.add_once_reminder(msg, target_dt_str, freq)
                                        freq_str = f" (Sıklık: {freq} dk)" if freq > 0 else " (Tek seferlik)"
                                        resp = f"⏰ Zamanlanmış hatırlatıcı kuruldu (ID: `{r_id}`):\nTarih: {target_dt_str}{freq_str}\nMesaj: '{msg}'"
                                    except Exception as e:
                                        resp = f"❌ Hata: {str(e)}"
                                else:
                                    resp = "❌ Hata. Zamanlı hatırlatıcı formatı: `/rem once <tarih> <saat> <sıklık_dk> <mesaj>`. Örn: `/rem once 22.06.2026 14:00 15 Hastane randevusu`"
                            else:
                                resp = "❌ Geçersiz mod. Seçenekler: `recurrent` (veya `tekrar`), `once` (veya `zamanli`)."
                        else:
                            resp = (
                                "❌ Eksik parametreler.\n\n"
                                "1️⃣ *Tekrarlı kurmak için:*\n`/rem tekrar <dakika> <mesaj>`\n"
                                "2️⃣ *Zamanlı kurmak için:*\n`/rem zamanli <tarih> <saat> <sıklık_dakika> <mesaj>`\n"
                                "Örnek: `/rem zamanli 22.06.2026 14:00 15 Muayene`"
                            )
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Roles Command (/roles)
                    if text_lower == "/roles":
                        active_role = role_var.get()
                        inline_keyboard = {"inline_keyboard": []}
                        for r_name in roles_dict:
                            status_prefix = "👉 " if r_name == active_role else ""
                            inline_keyboard["inline_keyboard"].append([
                                {"text": f"{status_prefix}{r_name} Olarak Ayarla", "callback_data": f"setrole:{r_name}"}
                            ])
                            
                        resp = "🎭 *Mevcut Yapay Zeka Rolleri:*\n\nAşağıdaki butonlara tıklayarak yapay zekanın aktif karakterini anında değiştirebilirsiniz:"
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id, 
                            "text": resp, 
                            "parse_mode": "Markdown",
                            "reply_markup": inline_keyboard
                        })
                        continue

                    # Set Role Command (/setrole)
                    if text_lower.startswith("/setrole "):
                        target_role = text.split(" ", 1)[1].strip()
                        matched_role = None
                        for r_name in roles_dict:
                            if r_name.lower() == target_role.lower():
                                matched_role = r_name
                                break
                        if matched_role:
                            set_role_cb(matched_role)
                            log_cb(f"[TELEGRAM] Yapay zeka rolü değiştirildi: {matched_role}", "system")
                            resp = f"👤 Yapay zeka rolü *{matched_role}* olarak değiştirildi."
                        else:
                            resp = "❌ Belirtilen rol bulunamadı. `/roles` yazarak listeyi görebilirsiniz."
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Set Auth PIN Command (/setpin)
                    if text_lower.startswith("/setpin ") or text_lower.startswith("/sifredegistir "):
                        parts = text.split(" ", 1)
                        new_pin_val = parts[1].strip()
                        if not new_pin_val:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Lütfen yeni bir şifre girin. Örn: `/setpin 999999`", "parse_mode": "Markdown"})
                            continue
                        try:
                            env_lines = []
                            if os.path.exists(".env"):
                                with open(".env", "r", encoding="utf-8") as f:
                                    env_lines = f.readlines()
                            found_pin_line = False
                            for idx, line in enumerate(env_lines):
                                if line.strip().startswith("TELEGRAM_AUTH_PIN="):
                                    env_lines[idx] = f"TELEGRAM_AUTH_PIN={new_pin_val}\n"
                                    found_pin_line = True
                                    break
                            if not found_pin_line:
                                env_lines.append(f"TELEGRAM_AUTH_PIN={new_pin_val}\n")
                            with open(".env", "w", encoding="utf-8") as f:
                                f.writelines(env_lines)
                            
                            auth_pin = new_pin_val
                            log_cb(f"[TELEGRAM] Yetkilendirme şifresi uzaktan güncellendi: {new_pin_val}", "system")
                            resp = f"✅ Yetkilendirme şifresi başarıyla *{new_pin_val}* olarak değiştirildi."
                        except Exception as e:
                            resp = f"❌ Şifre güncellenirken hata oluştu: {str(e)}"
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": resp, "parse_mode": "Markdown"})
                        continue

                    # Spotify Command (/spotify)
                    if text_lower.startswith("/spotify "):
                        q = text.split(" ", 1)[1].strip()
                        run_cmd_cb(f"spotify:{q}")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🎵 Spotify'da aranıyor: '{q}'"})
                        continue

                    # Brightness Command
                    if text_lower.startswith("/brightness "):
                        try:
                            val = int(text.split(" ", 1)[1].strip())
                            system_utils.set_brightness(val)
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🔆 Parlaklık %{val} olarak ayarlandı."})
                        except Exception as e:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Geçersiz değer: {str(e)}"})
                        continue

                    # Power Plan Command
                    if text_lower.startswith("/power "):
                        mode = text.split(" ", 1)[1].strip().lower()
                        if mode == "high":
                            mode = "high_performance"
                        if mode in ("balanced", "high_performance", "saver"):
                            system_utils.set_power_plan(mode)
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🔋 Güç planı değiştirildi: {mode}"})
                        else:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Geçersiz plan. Seçenekler: `balanced`, `high`, `saver`."})
                        continue

                    # Say/TTS Command
                    if text_lower.startswith("/say "):
                        say_text = text.split(" ", 1)[1].strip()
                        clean_text = say_text.replace('"', "'").replace("\n", " ")
                        ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{clean_text}")'
                        subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        log_cb(f"[TELEGRAM] Seslendirme komutu: {say_text}", "system")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🔊 PC'de seslendiriliyor: '{say_text}'"})
                        continue

                    # File List (ls) Command (Interactive Touch-based Explorer)
                    if text_lower.startswith("/ls") or text_lower == "/ls":
                        parts = text.split(" ", 1)
                        target_dir = parts[1].strip() if len(parts) > 1 else os.getcwd()
                        
                        info_text, markup = get_ls_markup(target_dir)
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id, 
                            "text": info_text, 
                            "parse_mode": "Markdown",
                            "reply_markup": markup
                        })
                        continue

                    # Download File Command
                    if text_lower.startswith("/download "):
                        target_file = text.split(" ", 1)[1].strip().replace('"', '')
                        if os.path.exists(target_file) and os.path.isfile(target_file):
                            log_cb(f"[TELEGRAM] {username} dosya indirme talebinde bulundu: {target_file}", "system")
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "📤 Dosya hazırlanıyor, gönderiliyor..."})
                            try:
                                with open(target_file, "rb") as f:
                                    requests.post(send_doc_url, data={"chat_id": chat_id}, files={"document": f})
                            except Exception as e:
                                requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Dosya gönderilirken hata oluştu: {str(e)}"})
                        else:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Belirtilen dosya bulunamadı veya klasör."})
                        continue

                    # Execute shell command (/cmd)
                    if text_lower.startswith("/cmd "):
                        cmd_to_run = text.split(" ", 1)[1].strip()
                        log_cb(f"[TELEGRAM] {username} CMD komutu gönderdi: {cmd_to_run}", "warn")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": "💻 Komut çalıştırılıyor..."})
                        try:
                            res = subprocess.run(cmd_to_run, shell=True, capture_output=True, text=True, timeout=10, encoding="cp857")
                            stdout = res.stdout if res.stdout else ""
                            stderr = res.stderr if res.stderr else ""
                            output = stdout + stderr
                            if not output.strip():
                                output = "(Komut çıktı vermedi)"
                            
                            if len(output) > 3500:
                                output = output[:3500] + "\n... (Çıktı çok uzun olduğu için kesildi)"
                            
                            requests.post(send_msg_url, json={
                                "chat_id": chat_id,
                                "text": f"📋 *Çıktı (Kod {res.returncode}):*\n```\n{output}\n```",
                                "parse_mode": "Markdown"
                            })
                        except subprocess.TimeoutExpired:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Hata: Komut zaman aşımına uğradı (10 saniye)."})
                        except Exception as e:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Komut çalıştırılırken hata oluştu: {str(e)}"})
                        continue

                    # List processes (/ps)
                    if text_lower in ("/ps", "/tasks"):
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": "📋 Süreçler taranıyor..."})
                        try:
                            res = subprocess.run("tasklist", shell=True, capture_output=True, text=True, encoding="cp857")
                            lines = res.stdout.split("\n")
                            output = "\n".join(lines[:35])
                            if len(lines) > 35:
                                output += f"\n... ve {len(lines) - 35} süreç daha."
                            
                            requests.post(send_msg_url, json={
                                "chat_id": chat_id,
                                "text": f"📋 *Çalışan Süreçler:*\n```\n{output}\n```",
                                "parse_mode": "Markdown"
                            })
                        except Exception as e:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Süreç listesi alınamadı: {str(e)}"})
                        continue

                    # Kill process
                    if text_lower.startswith("/kill "):
                        proc_name = text.split(" ", 1)[1].strip()
                        log_cb(f"[TELEGRAM] {username} süreç sonlandırma talebinde bulundu: {proc_name}", "warn")
                        try:
                            res = subprocess.run(f"taskkill /f /im {proc_name}", shell=True, capture_output=True, text=True, encoding="cp857")
                            if res.returncode == 0:
                                requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"✅ Süreç başarıyla sonlandırıldı: {proc_name}"})
                            else:
                                requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Sonlandırılamadı:\n`{res.stderr.strip()}`", "parse_mode": "Markdown"})
                        except Exception as e:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Hata: {str(e)}"})
                        continue

                    # Webcam Capture Command (/cam)
                    if text_lower == "/cam":
                        log_cb(f"[TELEGRAM] {username} kamera görüntüsü talep etti.", "system")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": "📷 Kamera açılıyor, fotoğraf çekiliyor..."})
                        temp_cam_path = "temp_telegram_cam.jpg"
                        if system_utils.capture_webcam(temp_cam_path):
                            try:
                                with open(temp_cam_path, "rb") as photo_file:
                                    requests.post(send_photo_url, data={"chat_id": chat_id}, files={"photo": photo_file})
                            except Exception as e:
                                requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"❌ Fotoğraf gönderilemedi: {str(e)}"})
                            finally:
                                if os.path.exists(temp_cam_path):
                                    os.remove(temp_cam_path)
                        else:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Kamera görüntüsü alınamadı. Kameranın bağlı ve aktif olduğundan emin olun."})
                        continue

                    # Shutdown Command (/shutdown)
                    if text_lower == "/shutdown":
                        inline_keyboard = {
                            "inline_keyboard": [
                                [
                                    {"text": "Evet, Kapat 🔌", "callback_data": "power:shutdown_confirm"},
                                    {"text": "İptal Et ❌", "callback_data": "power:cancel"}
                                ]
                            ]
                        }
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id,
                            "text": "⚠️ *UYARI:* Bilgisayarı kapatmak istediğinizden emin misiniz?",
                            "parse_mode": "Markdown",
                            "reply_markup": inline_keyboard
                        })
                        continue

                    # Restart Command (/restart)
                    if text_lower == "/restart":
                        inline_keyboard = {
                            "inline_keyboard": [
                                [
                                    {"text": "Evet, Yeniden Başlat 🔄", "callback_data": "power:restart_confirm"},
                                    {"text": "İptal Et ❌", "callback_data": "power:cancel"}
                                ]
                            ]
                        }
                        requests.post(send_msg_url, json={
                            "chat_id": chat_id,
                            "text": "⚠️ *UYARI:* Bilgisayarı yeniden başlatmak istediğinizden emin misiniz?",
                            "parse_mode": "Markdown",
                            "reply_markup": inline_keyboard
                        })
                        continue

                    # Default quick commands mapping
                    sys_actions = {
                        "/lock": "lock",
                        "/sleep": "sleep",
                        "/mute": "volume_mute",
                        "/volup": "volume_up",
                        "/voldown": "volume_down",
                        "/play": "media_play_pause"
                    }
                    if text_lower in sys_actions:
                        action = sys_actions[text_lower]
                        system_utils.execute_system_cmd(action)
                        log_cb(f"[TELEGRAM] {username} sistem komutu çalıştırdı: {text}", "system")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"✅ Komut çalıştırıldı: {text}"})
                        continue

                    if text_lower == "/screen":
                        log_cb(f"[TELEGRAM] {username} ekran görüntüsü talep etti.", "system")
                        temp_path = "temp_telegram_screen.png"
                        if system_utils.take_screenshot(temp_path):
                            try:
                                with open(temp_path, "rb") as photo_file:
                                    requests.post(send_photo_url, data={"chat_id": chat_id}, files={"photo": photo_file})
                            finally:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                        else:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❌ Ekran görüntüsü alınamadı."})
                        continue

                    # Custom system shortcuts from command.json
                    try:
                        with open("command.json", "r", encoding="utf-8") as f:
                            cmds = json.load(f)
                    except Exception:
                        cmds = {}

                    if text_lower in cmds:
                        run_cmd_cb(text)
                        log_cb(f"[TELEGRAM] {username} kısayol çalıştırdı: {text}", "system")
                        requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🚀 Kısayol çalıştırıldı: {text}"})
                        continue

                    # Web Search
                    if text_lower.startswith("bul ") or text_lower == "bul":
                        query = text[4:].strip() if text_lower.startswith("bul ") else ""
                        if query:
                            log_cb(f"[TELEGRAM] {username} arama yapıyor: {query}", "system")
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": f"🔍 Wikipedia ve Gemini üzerinde '{query}' aranıyor..."})
                            
                            from search_bot import web_search_and_summarize
                            active_role = role_var.get()
                            system_instruction = roles_dict.get(active_role, None)
                            ans, sources = web_search_and_summarize(query, system_instruction=system_instruction)
                            
                            update_last_response_cb(ans)
                            log_cb(f"\n[JARVIS - Telegram Arama]\n{ans}\n", "system")
                            
                            reply = ans
                            if sources:
                                reply += "\n\n[Kaynaklar]:\n" + "\n".join([f"- {title}: {uri}" for title, uri in sources])
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": reply})
                        else:
                            requests.post(send_msg_url, json={"chat_id": chat_id, "text": "❓ Ne bulmak istiyorsunuz?"})
                        continue

                    # Default: Gemini Chatbot
                    log_cb(f"[TELEGRAM] {username} mesaj gönderdi: {text}", "system")
                    requests.post(send_msg_url, json={"chat_id": chat_id, "text": "🤔 Düşünüyor..."})
                    
                    from search_bot import ask_gemini
                    active_role = role_var.get()
                    system_instruction = roles_dict.get(active_role, None)
                    ans = ask_gemini(text, system_instruction=system_instruction)
                    
                    update_last_response_cb(ans)
                    log_cb(f"\n[JARVIS - Telegram Chat]\n{ans}\n", "system")
                    requests.post(send_msg_url, json={"chat_id": chat_id, "text": ans})

            except Exception as e:
                log_cb(f"[TELEGRAM HATA] {str(e)}", "error")
                time.sleep(10)

    threading.Thread(target=bot_loop, daemon=True).start()
