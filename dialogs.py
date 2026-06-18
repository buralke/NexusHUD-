import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import threading

CYAN = "#00f3ff"
DARK_CYAN = "#005f73"
BG = "#060913"
SIDEBAR_BG = "#0d111f"
BORDER_COLOR = "#1a2538"
GREEN = "#00ff66"
DARK_GREEN = "#006622"
RED = "#ff0055"
AMBER = "#ffaa00"
FONT = ("Consolas", 11)
FONT_SMALL = ("Consolas", 9)

def show_roles_dialog(root, roles_dict, refresh_roles_menu_cb, log_cb):
    dialog = tk.Toplevel(root)
    dialog.title("Rol Yönetimi")
    dialog.geometry("500x350")
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 500) // 2
    y = root.winfo_y() + (root.winfo_height() - 350) // 2
    dialog.geometry(f"+{x}+{y}")

    # Sol tarafta liste, sağ tarafta ekleme formu
    left_frame = tk.Frame(dialog, bg=BG)
    left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

    tk.Label(left_frame, text="Mevcut Roller", bg=BG, fg=CYAN, font=FONT_SMALL).pack(anchor="w", pady=(0, 5))

    list_container = tk.Frame(left_frame, bg=BG)
    list_container.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(list_container)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(list_container, bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, relief="flat", yscrollcommand=scrollbar.set, selectbackground="#14223d", selectforeground=CYAN)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    def populate_listbox():
        listbox.delete(0, "end")
        for r_name in roles_dict:
            listbox.insert("end", r_name)

    populate_listbox()

    # Ekleme formu (Sağ taraf)
    right_frame = tk.Frame(dialog, bg=BG)
    right_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)

    tk.Label(right_frame, text="Rol Adı", bg=BG, fg=CYAN, font=FONT_SMALL).pack(anchor="w")
    name_entry = tk.Entry(right_frame, bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, relief="flat", bd=2)
    name_entry.pack(fill="x", pady=(0, 10))

    tk.Label(right_frame, text="Sistem Talimatı", bg=BG, fg=CYAN, font=FONT_SMALL).pack(anchor="w")
    instruction_text = tk.Text(right_frame, bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, relief="flat", bd=2, height=6, wrap="word", insertbackground=CYAN)
    instruction_text.pack(fill="both", expand=True, pady=(0, 10))

    def add_new_role():
        name = name_entry.get().strip()
        instr = instruction_text.get("1.0", "end").strip()
        if not name or not instr:
            messagebox.showerror("Hata", "Lütfen rol adı ve talimatı doldurun.", parent=dialog)
            return
            
        try:
            with open("roles.json", "r", encoding="utf-8") as f:
                r_dict = json.load(f)
            r_dict[name] = instr
            with open("roles.json", "w", encoding="utf-8") as f:
                json.dump(r_dict, f, indent=2, ensure_ascii=False)
            
            roles_dict[name] = instr
            refresh_roles_menu_cb()
            populate_listbox()
            name_entry.delete(0, "end")
            instruction_text.delete("1.0", "end")
            log_cb(f"[SİSTEM] Yeni rol eklendi: {name}", "system")
        except Exception as e:
            messagebox.showerror("Hata", f"Rol kaydedilemedi: {str(e)}", parent=dialog)

    def delete_selected_role():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Hata", "Lütfen silmek için bir rol seçin.", parent=dialog)
            return
        r_name = listbox.get(selection[0])
        if r_name == "Jarvis":
            messagebox.showerror("Hata", "Varsayılan Jarvis rolü silinemez.", parent=dialog)
            return
            
        try:
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
            messagebox.showerror("Hata", f"Rol silinemedi: {str(e)}", parent=dialog)

    add_btn_action = tk.Button(right_frame, text="Rolü Ekle", bg="#112519", fg=GREEN, font=FONT_SMALL, relief="flat", command=add_new_role)
    add_btn_action.pack(fill="x", pady=2)

    del_btn_action = tk.Button(left_frame, text="Seçileni Sil", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=delete_selected_role)
    del_btn_action.pack(fill="x", pady=(10, 0))


def show_api_settings_dialog(root, update_api_status_cb, log_cb):
    dialog = tk.Toplevel(root)
    dialog.title("Gemini API Ayarları")
    dialog.geometry("400x200")
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 400) // 2
    y = root.winfo_y() + (root.winfo_height() - 200) // 2
    dialog.geometry(f"+{x}+{y}")

    tk.Label(dialog, text="Gemini API Anahtarı", bg=BG, fg=CYAN, font=FONT_SMALL).pack(pady=(20, 5), padx=20, anchor="w")
    
    from dotenv import load_dotenv
    load_dotenv()
    current_key = os.getenv("GEMINI_API_KEY", "")
    if current_key.startswith("YOUR_GEMINI_API_KEY"):
        current_key = ""

    key_entry = tk.Entry(dialog, bg=SIDEBAR_BG, fg=CYAN, font=FONT, insertbackground=CYAN, relief="flat", bd=2, show="*")
    key_entry.pack(fill="x", padx=20, pady=(0, 10))
    key_entry.insert(0, current_key)
    key_entry.focus_set()

    show_var = tk.BooleanVar(value=False)
    def toggle_show():
        if show_var.get():
            key_entry.config(show="")
        else:
            key_entry.config(show="*")
            
    show_cb = tk.Checkbutton(dialog, text="Anahtarı Göster", variable=show_var, bg=BG, fg=DARK_CYAN, activebackground=BG, activeforeground=CYAN, selectcolor=BG, font=FONT_SMALL, command=toggle_show)
    show_cb.pack(padx=20, anchor="w")

    def save_api_key():
        new_key = key_entry.get().strip()
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
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"API anahtarı kaydedilemedi: {str(e)}", parent=dialog)

    save_btn = tk.Button(dialog, text="Kaydet", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=save_api_key)
    save_btn.pack(fill="x", padx=20, pady=15)


def show_add_dialog(root, refresh_sidebar_cb, log_cb):
    dialog = tk.Toplevel(root)
    dialog.title("Komut Ekle")
    dialog.geometry("400x220")
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 400) // 2
    y = root.winfo_y() + (root.winfo_height() - 220) // 2
    dialog.geometry(f"+{x}+{y}")

    tk.Label(dialog, text="Kısayol Adı (örn: google)", bg=BG, fg=CYAN, font=FONT_SMALL).pack(pady=(15, 2), padx=20, anchor="w")
    key_entry = tk.Entry(dialog, bg=SIDEBAR_BG, fg=CYAN, font=FONT, insertbackground=CYAN, relief="flat", bd=2)
    key_entry.pack(fill="x", padx=20, pady=(0, 10))
    key_entry.focus_set()

    tk.Label(dialog, text="Komut / URL veya Dosya Yolu", bg=BG, fg=CYAN, font=FONT_SMALL).pack(pady=(5, 2), padx=20, anchor="w")
    val_frame = tk.Frame(dialog, bg=BG)
    val_frame.pack(fill="x", padx=20, pady=(0, 15))

    val_entry = tk.Entry(val_frame, bg=SIDEBAR_BG, fg=CYAN, font=FONT, insertbackground=CYAN, relief="flat", bd=2)
    val_entry.pack(side="left", fill="x", expand=True)

    def select_file():
        file_path = filedialog.askopenfilename(
            parent=dialog,
            title="Dosya veya Uygulama Seç",
            filetypes=[("Tüm Dosyalar (*.*)", "*.*"), ("Uygulamalar (*.exe)", "*.exe"), ("Kısayollar (*.lnk)", "*.lnk")]
        )
        if file_path:
            norm_path = os.path.normpath(file_path)
            val_entry.delete(0, "end")
            val_entry.insert(0, f'"{norm_path}"')

    select_btn = tk.Button(val_frame, text="Gözat...", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", activebackground="#1e2d4a", activeforeground=CYAN, command=select_file)
    select_btn.pack(side="right", padx=(5, 0))

    def save_cmd():
        k = key_entry.get().strip().lower()
        v = val_entry.get().strip()
        if not k or not v:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.", parent=dialog)
            return
        
        try:
            with open("command.json", "r", encoding="utf-8") as f:
                current_cmds = json.load(f)
            current_cmds[k] = v
            with open("command.json", "w", encoding="utf-8") as f:
                json.dump(current_cmds, f, indent=2, ensure_ascii=False)
            
            refresh_sidebar_cb()
            log_cb(f"[SİSTEM] Yeni komut eklendi: {k}", "system")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}", parent=dialog)

    save_btn = tk.Button(dialog, text="Kaydet", bg="#112519", fg=GREEN, font=FONT_SMALL, relief="flat", command=save_cmd)
    save_btn.pack(fill="x", padx=20, pady=5)


def show_delete_dialog(root, cmds, refresh_sidebar_cb, log_cb):
    dialog = tk.Toplevel(root)
    dialog.title("Komut Sil")
    dialog.geometry("300x250")
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 300) // 2
    y = root.winfo_y() + (root.winfo_height() - 250) // 2
    dialog.geometry(f"+{x}+{y}")

    tk.Label(dialog, text="Silinecek Komutu Seçin", bg=BG, fg=CYAN, font=FONT_SMALL).pack(pady=(15, 5), padx=20, anchor="w")

    list_frame = tk.Frame(dialog, bg=BG)
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(list_frame, bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, relief="flat", yscrollcommand=scrollbar.set, selectbackground="#14223d", selectforeground=CYAN)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    for k in cmds:
        listbox.insert("end", k)

    def delete_cmd():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Hata", "Lütfen silinecek bir komut seçin.", parent=dialog)
            return
        
        k = listbox.get(selection[0])
        
        try:
            with open("command.json", "r", encoding="utf-8") as f:
                current_cmds = json.load(f)
            if k in current_cmds:
                del current_cmds[k]
            with open("command.json", "w", encoding="utf-8") as f:
                json.dump(current_cmds, f, indent=2, ensure_ascii=False)
            
            refresh_sidebar_cb()
            log_cb(f"[SİSTEM] Komut silindi: {k}", "warn")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {str(e)}", parent=dialog)

    del_btn = tk.Button(dialog, text="Seçileni Sil", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=delete_cmd)
    del_btn.pack(fill="x", padx=20, pady=10)


def show_desktop_image_analysis(root, role_var, roles_dict, log_cb, update_last_response_cb):
    file_path = filedialog.askopenfilename(
        title="Analiz Edilecek Görseli Seçin",
        filetypes=[("Görseller", "*.png *.jpg *.jpeg *.webp *.gif")]
    )
    if not file_path:
        return
        
    prompt_dialog = tk.Toplevel(root)
    prompt_dialog.title("Görsel Analiz Sorusu")
    prompt_dialog.geometry("400x180")
    prompt_dialog.configure(bg=BG)
    prompt_dialog.resizable(False, False)
    prompt_dialog.transient(root)
    prompt_dialog.grab_set()
    
    x = root.winfo_x() + (root.winfo_width() - 400) // 2
    y = root.winfo_y() + (root.winfo_height() - 180) // 2
    prompt_dialog.geometry(f"+{x}+{y}")
    
    tk.Label(prompt_dialog, text="Görsel hakkında ne sormak istersiniz?", bg=BG, fg=CYAN, font=FONT_SMALL).pack(pady=(15, 5), padx=20, anchor="w")
    prompt_entry = tk.Entry(prompt_dialog, bg=SIDEBAR_BG, fg=CYAN, font=FONT, insertbackground=CYAN, relief="flat", bd=2)
    prompt_entry.pack(fill="x", padx=20, pady=(0, 15))
    prompt_entry.insert(0, "Bu fotoğrafta ne görüyorsun?")
    prompt_entry.focus_set()
    
    def analyze():
        prompt = prompt_entry.get().strip()
        if not prompt:
            return
        prompt_dialog.destroy()
        
        log_cb(f"[SİSTEM] Görsel analiz ediliyor ({os.path.basename(file_path)})...", "system")
        
        def do_analysis():
            try:
                with open(file_path, "rb") as img_f:
                    img_bytes = img_f.read()
                
                ext = os.path.splitext(file_path)[1].lower()
                if ext in (".png", ".webp", ".gif"):
                    mime = f"image/{ext[1:]}"
                else:
                    mime = "image/jpeg"
                    
                from search_bot import ask_gemini
                active_role = role_var.get()
                system_instruction = roles_dict.get(active_role, None)
                ans = ask_gemini(prompt, system_instruction=system_instruction, image_data={"mime_type": mime, "data": img_bytes})
                
                def update_ui():
                    update_last_response_cb(ans)
                    log_cb("\n[JARVIS - GÖRSEL ANALİZ]", "system")
                    log_cb(ans)
                    log_cb("")
                root.after(0, update_ui)
            except Exception as e:
                root.after(0, lambda: log_cb(f"[HATA] Görsel analiz edilemedi: {str(e)}", "error"))
                
        threading.Thread(target=do_analysis, daemon=True).start()
        
    btn_analiz = tk.Button(prompt_dialog, text="Analiz Et", bg="#112519", fg=GREEN, font=FONT_SMALL, relief="flat", command=analyze)
    btn_analiz.pack(fill="x", padx=20, pady=5)

def show_reminder_popup(root, message):
    popup = tk.Toplevel(root)
    popup.title("HATIRLATICI BİLDİRİMİ")
    popup.geometry("380x200")
    popup.configure(bg=BG, highlightbackground=RED, highlightthickness=2)
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 380) // 2
    y = root.winfo_y() + (root.winfo_height() - 200) // 2
    popup.geometry(f"+{x}+{y}")

    color_state = [True]

    title_label = tk.Label(popup, text="// UYARI: ZAMANLAYICI UYARISI", bg=BG, fg=RED, font=("Consolas", 11, "bold"))
    title_label.pack(pady=(20, 10))

    msg_label = tk.Label(popup, text=message, bg=BG, fg="#ffffff", font=("Consolas", 12), wrap=340)
    msg_label.pack(pady=10, padx=20, fill="both", expand=True)

    btn_ok = tk.Button(popup, text="TAMAM", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", activebackground=RED, activeforeground="#ffffff", command=popup.destroy)
    btn_ok.pack(pady=(10, 20), padx=50, fill="x")

    def blink():
        if not popup.winfo_exists():
            return
        if color_state[0]:
            popup.configure(highlightbackground=AMBER)
            title_label.config(fg=AMBER)
            btn_ok.config(fg=AMBER, bg="#332200")
        else:
            popup.configure(highlightbackground=RED)
            title_label.config(fg=RED)
            btn_ok.config(fg=RED, bg="#2c121c")
        color_state[0] = not color_state[0]
        popup.after(500, blink)

    blink()

def show_create_reminder_dialog(root, add_reminder_cb):
    dialog = tk.Toplevel(root)
    dialog.title("Zamanlayıcı Bildirimi")
    dialog.geometry("380x250")
    dialog.configure(bg=BG, highlightbackground=CYAN, highlightthickness=2)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # Ortala
    x = root.winfo_x() + (root.winfo_width() - 380) // 2
    y = root.winfo_y() + (root.winfo_height() - 250) // 2
    dialog.geometry(f"+{x}+{y}")

    tk.Label(dialog, text="// YENİ ZAMANLAYICI BİLDİRİMİ", bg=BG, fg=CYAN, font=("Consolas", 11, "bold")).pack(pady=(15, 10))

    tk.Label(dialog, text="Kaç dakika sonra?", bg=BG, fg=DARK_CYAN, font=FONT_SMALL).pack(anchor="w", padx=30)
    min_entry = tk.Entry(dialog, bg=SIDEBAR_BG, fg="#ffffff", font=FONT, insertbackground=CYAN, relief="flat", bd=2)
    min_entry.pack(fill="x", padx=30, pady=(0, 10))
    min_entry.insert(0, "5")
    min_entry.focus_set()

    tk.Label(dialog, text="Bildirim mesajı?", bg=BG, fg=DARK_CYAN, font=FONT_SMALL).pack(anchor="w", padx=30)
    msg_entry = tk.Entry(dialog, bg=SIDEBAR_BG, fg="#ffffff", font=FONT, insertbackground=CYAN, relief="flat", bd=2)
    msg_entry.pack(fill="x", padx=30, pady=(0, 15))
    msg_entry.insert(0, "Zaman doldu!")

    def on_save():
        minutes = min_entry.get().strip()
        message = msg_entry.get().strip()
        if not minutes or not message:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.", parent=dialog)
            return
        try:
            float(minutes)
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli bir dakika girin.", parent=dialog)
            return
        
        add_reminder_cb(minutes, message)
        dialog.destroy()

    btn_frame = tk.Frame(dialog, bg=BG)
    btn_frame.pack(fill="x", padx=30, pady=5)

    btn_cancel = tk.Button(btn_frame, text="İPTAL", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=dialog.destroy)
    btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 5))

    btn_save = tk.Button(btn_frame, text="KUR", bg="#112519", fg=GREEN, font=FONT_SMALL, relief="flat", command=on_save)
    btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))
