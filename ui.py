import tkinter as tk
from tkinter import messagebox
import json
import subprocess
import webbrowser
from datetime import datetime
import os
import threading
from urllib.parse import quote

# Import our custom modular files
import system_utils
import dialogs
import web_server

# Load command.json
try:
    with open("command.json", "r", encoding="utf-8") as f:
        cmds = json.load(f)
except Exception:
    cmds = {}

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

root = tk.Tk()
root.title("NexusHUD v0.1")
root.configure(bg=BG)
root.geometry("900x550")

sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=180, highlightbackground=BORDER_COLOR, highlightthickness=1)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="// KISAYOLLAR", bg=SIDEBAR_BG, fg=DARK_CYAN, font=FONT_SMALL).pack(pady=(10, 5), padx=10, anchor="w")

main = tk.Frame(root, bg=BG)
main.pack(side="left", fill="both", expand=True)

# Top Bar
top_bar = tk.Frame(main, bg=BG)
top_bar.pack(side="top", fill="x", padx=10, pady=(10, 0))

tk.Label(top_bar, text="// TERMİNAL", bg=BG, fg=DARK_CYAN, font=FONT_SMALL).pack(side="left")

status_btn = tk.Button(top_bar, text="● WIKIPEDIA SEARCH", bg=BG, fg=AMBER, font=FONT_SMALL, relief="flat", activebackground=BG, cursor="hand2")
status_btn.pack(side="right")

# Role management definitions
roles_dict = {}
role_var = tk.StringVar(root)

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
initial_roles = list(roles_dict.keys()) if roles_dict else ["Jarvis"]
role_var.set(initial_roles[0])

role_label = tk.Label(top_bar, text="ROL:", bg=BG, fg=DARK_CYAN, font=FONT_SMALL)
role_menu = tk.OptionMenu(top_bar, role_var, *initial_roles)
role_menu.config(bg=BG, fg=CYAN, activebackground=SIDEBAR_BG, activeforeground=CYAN, relief="flat", highlightthickness=0, font=FONT_SMALL)
role_menu["menu"].config(bg=BG, fg=CYAN, activebackground=SIDEBAR_BG, activeforeground=CYAN, font=FONT_SMALL)

def refresh_roles_menu():
    load_roles()
    menu = role_menu["menu"]
    menu.delete(0, "end")
    for r_name in roles_dict.keys():
        menu.add_command(label=r_name, command=lambda value=r_name: role_var.set(value))
    if role_var.get() not in roles_dict:
        role_var.set(next(iter(roles_dict.keys())))

def show_roles():
    dialogs.show_roles_dialog(root, roles_dict, refresh_roles_menu, log)

roles_btn = tk.Button(top_bar, text="[Roller]", bg=BG, fg=CYAN, font=FONT_SMALL, relief="flat", activebackground=BG, cursor="hand2", command=show_roles)

def show_api_settings():
    dialogs.show_api_settings_dialog(root, update_api_status, log)

status_btn.config(command=show_api_settings)

def update_api_status():
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "")
    if key and key.strip() and not key.startswith("YOUR_GEMINI_API_KEY"):
        import search_bot
        search_bot.configure_api(key)
        status_btn.config(text="● GEMINI API", fg=GREEN, activeforeground=GREEN)
        roles_btn.pack(side="right", padx=(10, 0))
        role_menu.pack(side="right", padx=(5, 0))
        role_label.pack(side="right", padx=(5, 0))
    else:
        import search_bot
        search_bot.configure_api(None)
        status_btn.config(text="● WIKIPEDIA SEARCH", fg=AMBER, activeforeground=AMBER)
        roles_btn.pack_forget()
        role_menu.pack_forget()
        role_label.pack_forget()

terminal = tk.Text(main, bg=BG, fg=CYAN, font=FONT, insertbackground=CYAN, state="disabled", wrap="word", relief="flat", bd=0)
terminal.pack(fill="both", expand=True, padx=10, pady=(5, 10))

terminal.tag_config("system", foreground=CYAN)
terminal.tag_config("input", foreground="#ffffff")
terminal.tag_config("error", foreground=RED)
terminal.tag_config("warn", foreground=AMBER)

input_frame = tk.Frame(main, bg=SIDEBAR_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
input_frame.pack(fill="x", padx=10, pady=(0, 10))

tk.Label(input_frame, text="JARVIS >", bg=SIDEBAR_BG, fg=CYAN, font=FONT).pack(side="left", padx=(5, 5))

cmd_input = tk.Entry(input_frame, bg=SIDEBAR_BG, fg="#ffffff", font=FONT, insertbackground=CYAN, relief="flat", bd=0)
cmd_input.pack(side="left", fill="x", expand=True, pady=6)

last_response = ""

def update_last_response(val):
    global last_response
    last_response = val

def speak_desktop(text):
    if not text:
        return
    clean_text = text.replace('"', "'").replace("\n", " ")
    ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{clean_text}")'
    subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

btn_read = tk.Button(input_frame, text="🔊 Oku", bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, relief="flat", activebackground="#14223d", activeforeground=CYAN, cursor="hand2", command=lambda: speak_desktop(last_response))
btn_read.pack(side="right", padx=5)

status_bar = tk.Frame(root, bg=SIDEBAR_BG, height=24, highlightbackground=BORDER_COLOR, highlightthickness=1)
status_bar.pack(side="bottom", fill="x")

status_label = tk.Label(status_bar, text="SİSTEM: AKTİF", bg=SIDEBAR_BG, fg=DARK_CYAN, font=FONT_SMALL)
status_label.pack(side="left", padx=10)

clock_label = tk.Label(status_bar, text="", bg=SIDEBAR_BG, fg=DARK_CYAN, font=FONT_SMALL)
clock_label.pack(side="right", padx=10)

def update_clock():
    clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
    root.after(1000, update_clock)

def log(text, tag=""):
    terminal.config(state="normal")
    terminal.insert("end", text + "\n", tag)
    terminal.see("end")
    terminal.config(state="disabled")

app_state = {
    "mode": "normal"
}

def run_cmd(cmd):
    global app_state, last_response
    cmd_clean = cmd.strip()
    cmd_lower = cmd_clean.lower()
    
    if cmd_lower.startswith("spotify:"):
        q = cmd_clean[8:].strip()
        url = f"https://open.spotify.com/search/{quote(q)}"
        log(f"[JARVIS] Spotify'da aranıyor: {q}", "system")
        webbrowser.open(url)
        return
    
    if app_state["mode"] == "search":
        app_state["mode"] = "normal"
        if not cmd_clean:
            log("[JARVIS] Arama iptal edildi.", "warn")
            return
        log("> " + cmd_clean, "input")
        log("[SİSTEM] İnternette aranıyor, lütfen bekleyin...", "warn")
        
        def do_search():
            from search_bot import web_search_and_summarize
            active_role = role_var.get()
            system_instruction = roles_dict.get(active_role, None)
            ans, sources = web_search_and_summarize(cmd_clean, system_instruction=system_instruction)
            
            update_last_response(ans)
            
            def update_ui():
                log("\n[JARVIS]", "system")
                log(ans)
                if sources:
                    log("\n[KAYNAKLAR]", "system")
                    for title, uri in sources:
                        log(f"- {title}: {uri}", "warn")
                log("")
            
            root.after(0, update_ui)
            
        threading.Thread(target=do_search, daemon=True).start()
        return

    log("> " + cmd_lower, "input")

    if cmd_lower in ("ex", "cik"):
        log("[JARVIS] Oturum sonlandırılıyor...", "warn")
        root.after(1000, root.destroy)
        return
    if cmd_lower in ("yardim", "help"):
        log("[JARVIS] Komutlar: bul, " + ", ".join(cmds.keys()), "system")
        return
    if cmd_lower in ("temizle", "cls"):
        terminal.config(state="normal")
        terminal.delete("1.0", "end")
        terminal.config(state="disabled")
        return
    if cmd_lower == "bul":
        app_state["mode"] = "search"
        log("[JARVIS] Ne bulmak istiyorsunuz?", "system")
        return

    if cmd_lower in cmds:
        val = cmds[cmd_lower]
        log("[JARVIS] Açılıyor: " + cmd_lower, "system")

        if val.startswith("http"):
            webbrowser.open(val)
        else:
            subprocess.Popen(val, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        log("[JARVIS] Düşünüyor...", "system")
        def ask_gemini_thread():
            from search_bot import ask_gemini
            active_role = role_var.get()
            system_instruction = roles_dict.get(active_role, None)
            ans = ask_gemini(cmd_clean, system_instruction=system_instruction)
            
            update_last_response(ans)
            
            def update_ui():
                log("\n[JARVIS]", "system")
                log(ans)
                log("")
            root.after(0, update_ui)
            
        threading.Thread(target=ask_gemini_thread, daemon=True).start()

def on_enter(event=None):
    text = cmd_input.get().strip()
    if text:
        run_cmd(text)
        cmd_input.delete(0, "end")

cmd_input.bind("<Return>", on_enter)

def create_fixed_btn(label, cmd_to_run):
    btn = tk.Button(
        sidebar, text="> " + label,
        bg=SIDEBAR_BG, fg=CYAN,
        font=FONT_SMALL, relief="flat",
        bd=0, anchor="w", padx=8,
        activebackground="#14223d",
        activeforeground=CYAN,
        cursor="hand2",
        command=lambda: run_cmd(cmd_to_run)
    )
    btn.pack(fill="x", pady=2, padx=6)

create_fixed_btn("bul", "bul")

cmd_buttons_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
cmd_buttons_frame.pack(fill="both", expand=True)

def refresh_sidebar():
    global cmds
    for widget in cmd_buttons_frame.winfo_children():
        widget.destroy()
    
    try:
        with open("command.json", "r", encoding="utf-8") as f:
            cmds = json.load(f)
    except Exception as e:
        log(f"[SİSTEM HATA] command.json okunamadı: {str(e)}", "error")
        return
        
    for k in cmds:
        btn = tk.Button(
            cmd_buttons_frame, text="> " + k,
            bg=SIDEBAR_BG, fg=CYAN,
            font=FONT_SMALL, relief="flat",
            bd=0, anchor="w", padx=8,
            activebackground="#14223d",
            activeforeground=CYAN,
            cursor="hand2",
            command=lambda l=k: run_cmd(l)
        )
        btn.pack(fill="x", pady=2, padx=6)

def show_add():
    dialogs.show_add_dialog(root, refresh_sidebar, log)

def show_delete():
    dialogs.show_delete_dialog(root, cmds, refresh_sidebar, log)

def show_desktop_image():
    dialogs.show_desktop_image_analysis(root, role_var, roles_dict, log, update_last_response)

# System Controls Sidebar Layout
tk.Label(sidebar, text="// SİSTEM KONTROLÜ", bg=SIDEBAR_BG, fg=DARK_CYAN, font=FONT_SMALL).pack(pady=(15, 5), padx=10, anchor="w")

control_grid = tk.Frame(sidebar, bg=SIDEBAR_BG)
control_grid.pack(fill="x", padx=6, pady=2)

btn_mute = tk.Button(control_grid, text="🔇 Sessiz", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("volume_mute"))
btn_mute.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

btn_play = tk.Button(control_grid, text="⏯ Oynat", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("media_play_pause"))
btn_play.grid(row=0, column=1, sticky="ew", padx=2, pady=2)

btn_vdown = tk.Button(control_grid, text="🔉 Ses -", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("volume_down"))
btn_vdown.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

btn_vup = tk.Button(control_grid, text="🔊 Ses +", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("volume_up"))
btn_vup.grid(row=1, column=1, sticky="ew", padx=2, pady=2)

btn_lock = tk.Button(control_grid, text="🔒 Kilitle", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("lock"))
btn_lock.grid(row=2, column=0, sticky="ew", padx=2, pady=2)

btn_sleep = tk.Button(control_grid, text="💤 Uyku", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=lambda: system_utils.execute_system_cmd("sleep"))
btn_sleep.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

control_grid.columnconfigure(0, weight=1)
control_grid.columnconfigure(1, weight=1)

btn_img_analiz = tk.Button(sidebar, text="📷 Görsel Analiz Et", bg="#14223d", fg=CYAN, font=FONT_SMALL, relief="flat", command=show_desktop_image)
btn_img_analiz.pack(fill="x", padx=6, pady=5)

# Metrics
metrics_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
metrics_frame.pack(side="bottom", fill="x", pady=(10, 5), padx=6)

cpu_lbl = tk.Label(metrics_frame, text="CPU YÜKÜ: --%", bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, anchor="w")
cpu_lbl.pack(fill="x")
ram_lbl = tk.Label(metrics_frame, text="RAM KULLAN: --%", bg=SIDEBAR_BG, fg=CYAN, font=FONT_SMALL, anchor="w")
ram_lbl.pack(fill="x")

def update_desktop_stats():
    cpu_lbl.config(text=f"CPU YÜKÜ: {system_utils.get_cpu_usage()}%")
    ram_lbl.config(text=f"RAM KULLAN: {system_utils.get_ram_usage()}%")
    root.after(3000, update_desktop_stats)

edit_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
edit_frame.pack(side="bottom", fill="x", pady=10, padx=6)

add_btn = tk.Button(edit_frame, text="+ Ekle", bg="#112519", fg=GREEN, font=FONT_SMALL, relief="flat", command=show_add)
add_btn.pack(side="left", fill="x", expand=True, padx=2)

del_btn = tk.Button(edit_frame, text="- Sil", bg="#2c121c", fg=RED, font=FONT_SMALL, relief="flat", command=show_delete)
del_btn.pack(side="right", fill="x", expand=True, padx=2)

refresh_sidebar()
update_api_status()
update_desktop_stats()

# Start the Web HUD server in a daemon thread
def start_server_in_thread():
    web_server.start_http_server(
        run_cmd_cb=lambda cmd: root.after(0, run_cmd, cmd),
        log_cb=lambda text, tag="": root.after(0, log, text, tag),
        roles_dict=roles_dict,
        get_cpu_cb=system_utils.get_cpu_usage,
        get_ram_cb=system_utils.get_ram_usage,
        exec_sys_cb=system_utils.execute_system_cmd,
        update_last_response_cb=update_last_response
    )

threading.Thread(target=start_server_in_thread, daemon=True).start()

log("    ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗", "system")
log("    ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝", "system")
log("    ██║███████║██████╔╝██║   ██║██║███████╗", "system")
log("██   ██║██╔══██║██╔══██║╚██╗ ██╔╝██║╚════██║", "system")
log("╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║", "system")
log(" ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝", "system")
log("")
log("[SİSTEM] v0.1 başlatılıyor...", "system")
log("[SİSTEM] " + str(len(cmds)) + " komut yüklendi.", "system")
log("[JARVIS] Hazır. Emredin.", "")

update_clock()
root.mainloop()
