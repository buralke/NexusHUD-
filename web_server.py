import json
import socket
import base64
import os
import threading
from urllib.parse import quote, unquote, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

class JarvisHTTPHandler(BaseHTTPRequestHandler):
    # Callback dependencies injected from main app
    run_cmd_cb = None
    log_cb = None
    roles_dict = {}
    get_cpu_usage_cb = None
    get_ram_usage_cb = None
    execute_system_cmd_cb = None
    update_last_response_cb = None

    # New premium callbacks
    get_clipboard_text_cb = None
    set_clipboard_text_cb = None
    get_brightness_cb = None
    set_brightness_cb = None
    set_power_plan_cb = None
    add_reminder_cb = None

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        if path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHUD Kontrol Merkezi</title>
    <style>
        body {
            background-color: #060913;
            color: #00f3ff;
            font-family: 'Consolas', monospace;
            margin: 0;
            padding: 15px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 450px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        h1 {
            font-size: 20px;
            text-align: center;
            margin: 10px 0;
            text-shadow: 0 0 10px #00f3ff;
            letter-spacing: 2px;
        }
        .card {
            background-color: #0d111f;
            border: 1px solid #1a2538;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        }
        .card-title {
            font-size: 13px;
            color: #005f73;
            margin-bottom: 10px;
            text-transform: uppercase;
            font-weight: bold;
            border-bottom: 1px solid #1a2538;
            padding-bottom: 5px;
        }
        /* Dashboard Stats */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .stat-box {
            text-align: center;
            padding: 10px;
            background-color: #080c16;
            border: 1px solid #1a2538;
            border-radius: 6px;
        }
        .stat-val {
            font-size: 24px;
            font-weight: bold;
            color: #00ff66;
            margin-top: 5px;
        }
        /* Buttons Grid */
        .btn-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .btn-system {
            background-color: #14223d;
            color: #00f3ff;
            border: 1px solid #00f3ff;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }
        .btn-system:active {
            background-color: #00f3ff;
            color: #060913;
        }
        .btn-red {
            border-color: #ff0055;
            color: #ff0055;
        }
        .btn-red:active {
            background-color: #ff0055;
            color: #ffffff;
        }
        /* Controls */
        input[type="text"], select, input[type="number"] {
            background-color: #080c16;
            color: #ffffff;
            border: 1px solid #1a2538;
            font-size: 14px;
            padding: 12px;
            width: 100%;
            box-sizing: border-box;
            border-radius: 6px;
            outline: none;
            margin-bottom: 10px;
        }
        input[type="text"]:focus, select:focus, input[type="number"]:focus {
            border-color: #00f3ff;
        }
        .flex-row {
            display: flex;
            gap: 8px;
        }
        .btn-action {
            background-color: #1a4a1a;
            color: #00ff66;
            border: 1px solid #00ff66;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 6px;
        }
        .btn-action:active {
            background-color: #00ff66;
            color: #080c16;
        }
        .btn-mic {
            background-color: #0d111f;
            border: 1px solid #00f3ff;
            color: #00f3ff;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .btn-mic.recording {
            background-color: #ff0055;
            border-color: #ff0055;
            color: #ffffff;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        /* Output & Image */
        .output-box {
            background-color: #080c16;
            border: 1px solid #1a2538;
            border-radius: 6px;
            padding: 12px;
            font-size: 13px;
            line-height: 1.5;
            max-height: 150px;
            overflow-y: auto;
            white-space: pre-wrap;
            margin-top: 10px;
            color: #a5b4fc;
        }
        #img-preview {
            max-width: 100%;
            max-height: 120px;
            display: none;
            margin-bottom: 10px;
            border-radius: 4px;
            border: 1px solid #1a2538;
        }
        /* File Explorer */
        .file-list {
            max-height: 200px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin-bottom: 10px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            background-color: #080c16;
            border: 1px solid #1a2538;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
        }
        .file-item:hover {
            border-color: #00f3ff;
        }
        .file-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-meta {
            color: #005f73;
            flex-shrink: 0;
            margin-left: 10px;
        }
        /* Slider */
        .slider-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        .slider-container input[type="range"] {
            flex: 1;
            accent-color: #00f3ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>NEXUSHUD H.U.D.</h1>
        
        <!-- PC Durumu & Hızlı Sistem Denetimi -->
        <div class="card">
            <div class="card-title">// Sistem Durumu & Ekran</div>
            <div class="stats-grid" style="margin-bottom: 15px;">
                <div class="stat-box">
                    <div>CPU YÜKÜ</div>
                    <div id="cpu-val" class="stat-val">--%</div>
                </div>
                <div class="stat-box">
                    <div>RAM KULLANIMI</div>
                    <div id="ram-val" class="stat-val">--%</div>
                </div>
            </div>
            
            <div class="slider-container">
                <span style="font-size: 12px; color: #005f73;">PARLAKLIK:</span>
                <input type="range" id="brightness" min="0" max="100" value="70" onchange="setBrightness(this.value)">
                <span id="brightness-val" style="font-size: 12px; width: 30px; text-align: right;">70%</span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 5px;">
                <span style="font-size: 12px; color: #005f73; margin-bottom: 3px;">GÜÇ PLANI:</span>
                <select id="power-plan" onchange="setPowerPlan(this.value)" style="margin-bottom: 0;">
                    <option value="balanced">Dengeli</option>
                    <option value="high_performance">Yüksek Performans</option>
                    <option value="saver">Güç Tasarrufu</option>
                </select>
            </div>
        </div>

        <!-- Yapay Zeka Komut / Sohbet -->
        <div class="card">
            <div class="card-title">// Yapay Zeka Arayüzü</div>
            <select id="role-select">
                <option value="Jarvis">Jarvis</option>
            </select>
            <div class="flex-row">
                <input type="text" id="cmd" placeholder="Mesaj veya komut yazın...">
                <button id="mic-btn" class="btn-mic" onclick="toggleRecognition()">🎤</button>
            </div>
            <div class="flex-row">
                <button onclick="sendCmd()" class="btn-action" style="flex: 1;">GÖNDER</button>
                <button onclick="speakLastResponse()" class="btn-system" style="flex: 0 0 auto; padding: 12px 15px;">🔊 Oku</button>
            </div>
            <div id="ai-output" class="output-box" style="display:none;"></div>
        </div>

        <!-- Görsel Analiz -->
        <div class="card">
            <div class="card-title">// Kamera & Görsel Analiz</div>
            <img id="img-preview" src="#">
            <div class="flex-row" style="margin-bottom: 10px;">
                <button class="btn-system" onclick="document.getElementById('file-input').click()">Fotoğraf Çek/Yükle</button>
                <input type="file" id="file-input" accept="image/*" style="display:none;" onchange="previewImage(this)">
            </div>
            <input type="text" id="img-prompt" placeholder="Görsel hakkında sorun..." value="Bu fotoğrafta ne görüyorsun?">
            <div class="flex-row">
                <button onclick="analyzeImage()" class="btn-action" style="flex: 1;">Görseli Analiz Et</button>
                <button onclick="speakLastImgResponse()" class="btn-system" style="flex: 0 0 auto; padding: 12px 15px;">🔊 Oku</button>
            </div>
            <div id="img-output" class="output-box" style="display:none;"></div>
        </div>

        <!-- Pano Paylaşımı (Clipboard) -->
        <div class="card">
            <div class="card-title">// Pano Paylaşımı (PC Clipboard)</div>
            <input type="text" id="clipboard-box" placeholder="Pano içeriği...">
            <div class="btn-grid">
                <button class="btn-system" onclick="getClipboard()">Panoyu Oku</button>
                <button class="btn-system" onclick="setClipboard()">Bilgisayara Yaz</button>
            </div>
        </div>

        <!-- Hatırlatıcı Zamanlayıcı -->
        <div class="card">
            <div class="card-title">// Zamanlayıcı Bildirim Kur</div>
            <input type="number" id="rem-min" placeholder="Kaç dakika sonra? (Örn: 5)" min="1" value="5">
            <input type="text" id="rem-msg" placeholder="Hatırlatma notu..." value="Zaman doldu!">
            <button class="btn-action" onclick="setReminder()" style="width: 100%;">Zamanlayıcıyı Başlat</button>
        </div>

        <!-- Dosya Gezgini -->
        <div class="card">
            <div class="card-title">// Uzaktan Dosya Gezgini</div>
            <div style="font-size: 11px; margin-bottom: 8px; word-break: break-all; color: #005f73;" id="curr-path">/</div>
            <button class="btn-system" onclick="goUpDir()" style="width: 100%; margin-bottom: 8px;">⬆ Üst Klasör</button>
            <div class="file-list" id="file-explorer"></div>
            <div class="flex-row" style="margin-top: 8px;">
                <button class="btn-system" onclick="document.getElementById('upload-input').click()" style="flex: 1;">Dosya Yükle</button>
                <input type="file" id="upload-input" style="display:none;" onchange="uploadFile(this)">
            </div>
        </div>

        <!-- Uzaktan Kumanda -->
        <div class="card">
            <div class="card-title">// Uzaktan Kumanda</div>
            <div class="btn-grid">
                <button class="btn-system" onclick="sendSys('volume_up')">🔊 SES +</button>
                <button class="btn-system" onclick="sendSys('volume_down')">🔉 SES -</button>
                <button class="btn-system" onclick="sendSys('volume_mute')">🔇 SESSİZ</button>
                <button class="btn-system" onclick="sendSys('media_play_pause')">⏯ OYNAT/DURDUR</button>
                <button class="btn-system btn-red" onclick="sendSys('lock')">🔒 KİLİTLE</button>
                <button class="btn-system btn-red" onclick="sendSys('sleep')">💤 UYKU MODU</button>
            </div>
        </div>
    </div>

    <script>
        let lastResponseText = "";
        let lastImgResponseText = "";
        let currentPath = "";

        // Rolleri Çek
        fetch('/roles')
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById("role-select");
                select.innerHTML = "";
                data.forEach(r => {
                    const opt = document.createElement("option");
                    opt.value = r;
                    opt.innerText = r;
                    select.appendChild(opt);
                });
            });

        // Canlı Metrik Güncellemesi
        function updateStats() {
            fetch('/stats')
                .then(res => res.json())
                .then(data => {
                    document.getElementById("cpu-val").innerText = data.cpu + "%";
                    document.getElementById("ram-val").innerText = data.ram + "%";
                });
        }
        setInterval(updateStats, 3000);
        updateStats();

        // Parlaklık ve Güç Ayarları
        function getBrightness() {
            fetch('/brightness')
                .then(res => res.json())
                .then(data => {
                    document.getElementById("brightness").value = data.brightness;
                    document.getElementById("brightness-val").innerText = data.brightness + "%";
                });
        }
        getBrightness();

        function setBrightness(val) {
            document.getElementById("brightness-val").innerText = val + "%";
            fetch('/brightness', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ brightness: val })
            });
        }

        function setPowerPlan(mode) {
            fetch('/power', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode })
            });
        }

        // Clipboard
        function getClipboard() {
            fetch('/clipboard')
                .then(res => res.json())
                .then(data => {
                    document.getElementById("clipboard-box").value = data.text;
                });
        }

        function setClipboard() {
            const val = document.getElementById("clipboard-box").value;
            fetch('/clipboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: val })
            }).then(() => alert("PC panosu güncellendi!"));
        }

        // Reminders
        function setReminder() {
            const min = document.getElementById("rem-min").value;
            const msg = document.getElementById("rem-msg").value;
            fetch('/reminder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ minutes: min, message: msg })
            }).then(() => alert(min + " dakika sonra hatırlatılacak."));
        }

        // File Explorer
        function loadDirectory(path) {
            let url = '/files';
            if (path) {
                url += '?path=' + encodeURIComponent(path);
            }
            fetch(url)
                .then(res => res.json())
                .then(data => {
                    currentPath = data.current_path;
                    document.getElementById("curr-path").innerText = currentPath;
                    
                    const explorer = document.getElementById("file-explorer");
                    explorer.innerHTML = "";
                    
                    data.items.forEach(item => {
                        const div = document.createElement("div");
                        div.className = "file-item";
                        
                        const nameSpan = document.createElement("span");
                        nameSpan.className = "file-name";
                        nameSpan.innerText = (item.is_dir ? "📁 " : "📄 ") + item.name;
                        
                        const metaSpan = document.createElement("span");
                        metaSpan.className = "file-meta";
                        metaSpan.innerText = item.is_dir ? "Klasör" : formatBytes(item.size);
                        
                        div.appendChild(nameSpan);
                        div.appendChild(metaSpan);
                        
                        div.onclick = () => {
                            if (item.is_dir) {
                                loadDirectory(currentPath + "/" + item.name);
                            } else {
                                window.open('/download?file=' + encodeURIComponent(currentPath + "/" + item.name));
                            }
                        };
                        explorer.appendChild(div);
                    });
                });
        }

        function goUpDir() {
            if (currentPath) {
                let parts = currentPath.split(/[\\/]/);
                parts.pop();
                let parent = parts.join("/");
                if (parent.trim() === "") parent = "/";
                loadDirectory(parent);
            }
        }

        function uploadFile(input) {
            const file = input.files[0];
            if (!file) return;
            
            const btn = event.target;
            
            fetch('/upload?filename=' + encodeURIComponent(file.name) + '&dest=' + encodeURIComponent(currentPath), {
                method: 'POST',
                body: file
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("Dosya başarıyla yüklendi!");
                    loadDirectory(currentPath);
                } else {
                    alert("Dosya yüklenemedi: " + data.message);
                }
            })
            .catch(() => alert("Dosya yükleme hatası."));
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        loadDirectory("");

        // Sesli Yanıt (TTS) fonksiyonu
        function speak(text) {
            const synth = window.speechSynthesis;
            synth.cancel(); // Mevcut konuşmayı kes
            const utter = new SpeechSynthesisUtterance(text);
            utter.lang = "tr-TR";
            synth.speak(utter);
        }

        function speakLastResponse() {
            if (lastResponseText) {
                speak(lastResponseText);
            } else {
                alert("Henüz okunacak bir yanıt yok.");
            }
        }

        // Ses Tanıma (Speech Recognition)
        let recognition;
        let isRecording = false;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.lang = 'tr-TR';
            
            recognition.onresult = function(event) {
                const result = event.results[0][0].transcript;
                document.getElementById("cmd").value = result;
                toggleRecognition(false);
            };
            
            recognition.onerror = function() {
                toggleRecognition(false);
            };
            
            recognition.onend = function() {
                toggleRecognition(false);
            };
        }

        function toggleRecognition(forceState) {
            if (!recognition) {
                alert("Ses tanıma tarayıcınız tarafından desteklenmiyor.");
                return;
            }
            const btn = document.getElementById("mic-btn");
            isRecording = forceState !== undefined ? forceState : !isRecording;
            if (isRecording) {
                btn.classList.add("recording");
                recognition.start();
            } else {
                btn.classList.remove("recording");
                recognition.stop();
            }
        }

        // Komut Gönder
        function sendCmd() {
            const cmdInput = document.getElementById("cmd");
            const outputDiv = document.getElementById("ai-output");
            const role = document.getElementById("role-select").value;
            const command = cmdInput.value.trim();
            if(!command) return;

            outputDiv.style.display = "block";
            outputDiv.innerText = "Jarvis düşünüyor...";
            outputDiv.style.color = "#ffaa00";

            fetch("/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: command, role: role })
            })
            .then(res => res.json())
            .then(data => {
                outputDiv.innerText = data.response;
                outputDiv.style.color = "#00ff66";
                cmdInput.value = "";
                lastResponseText = data.response;
            })
            .catch(err => {
                outputDiv.innerText = "Komut gönderilemedi.";
                outputDiv.style.color = "#ff0055";
            });
        }

        // Sistem Eylemi Gönder
        function sendSys(action) {
            fetch("/system", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            });
        }

        // Resim Önizleme
        let base64Image = "";
        function previewImage(input) {
            const file = input.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.getElementById("img-preview");
                    img.src = e.target.result;
                    img.style.display = "block";
                    base64Image = e.target.result;
                }
                reader.readAsDataURL(file);
            }
        }

        // Görsel Analiz Yap
        function analyzeImage() {
            const outputDiv = document.getElementById("img-output");
            const prompt = document.getElementById("img-prompt").value;
            const role = document.getElementById("role-select").value;
            if (!base64Image) {
                alert("Lütfen önce bir fotoğraf çekin veya yükleyin.");
                return;
            }

            outputDiv.style.display = "block";
            outputDiv.innerText = "Jarvis görseli analiz ediyor...";
            outputDiv.style.color = "#ffaa00";

            fetch("/image", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: base64Image, prompt: prompt, role: role })
            })
            .then(res => res.json())
            .then(data => {
                outputDiv.innerText = data.response;
                outputDiv.style.color = "#00ff66";
                lastImgResponseText = data.response;
            })
            .catch(err => {
                outputDiv.innerText = "Analiz başarısız oldu.";
                outputDiv.style.color = "#ff0055";
            });
        }
    </script>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return
        elif path == "/stats":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            stats = {
                "cpu": JarvisHTTPHandler.get_cpu_usage_cb() if JarvisHTTPHandler.get_cpu_usage_cb else 0,
                "ram": JarvisHTTPHandler.get_ram_usage_cb() if JarvisHTTPHandler.get_ram_usage_cb else 0
            }
            self.wfile.write(json.dumps(stats).encode('utf-8'))
            return
        elif path == "/roles":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(list(JarvisHTTPHandler.roles_dict.keys())).encode('utf-8'))
            return
        elif path == "/brightness":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            brightness = JarvisHTTPHandler.get_brightness_cb() if JarvisHTTPHandler.get_brightness_cb else 70
            self.wfile.write(json.dumps({"brightness": brightness}).encode('utf-8'))
            return
        elif path == "/clipboard":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            text = JarvisHTTPHandler.get_clipboard_text_cb() if JarvisHTTPHandler.get_clipboard_text_cb else ""
            self.wfile.write(json.dumps({"text": text}).encode('utf-8'))
            return
        elif path == "/files":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            target_dir = query_params.get('path', [None])[0]
            if target_dir:
                target_dir = unquote(target_dir)
            else:
                target_dir = os.path.expanduser("~/Desktop")
                if not os.path.exists(target_dir):
                    target_dir = os.getcwd()
            
            items = []
            try:
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    for name in os.listdir(target_dir):
                        full_p = os.path.join(target_dir, name)
                        is_dir = os.path.isdir(full_p)
                        size = os.path.getsize(full_p) if not is_dir else 0
                        items.append({"name": name, "is_dir": is_dir, "size": size})
            except Exception:
                pass
            
            # Sort directories first, then files
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            
            self.wfile.write(json.dumps({
                "current_path": os.path.abspath(target_dir).replace("\\", "/"),
                "items": items
            }).encode('utf-8'))
            return
        elif path == "/download":
            file_path = query_params.get('file', [None])[0]
            if file_path:
                file_path = unquote(file_path)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                    self.end_headers()
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            self.send_response(404)
            self.end_headers()
            return
            
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        if path == "/command":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                command = data.get("command", "").strip()
                role = data.get("role", "Jarvis")
                system_instruction = JarvisHTTPHandler.roles_dict.get(role, None)
                
                response_text = ""
                cmd_lower = command.lower()
                
                if cmd_lower.startswith("spotify:") or cmd_lower in JarvisHTTPHandler.roles_dict or cmd_lower in ("ex", "cik", "yardim", "help", "temizle", "cls"):
                    if JarvisHTTPHandler.run_cmd_cb:
                        JarvisHTTPHandler.run_cmd_cb(command)
                    response_text = f"Komut tetiklendi: {command}"
                elif cmd_lower.startswith("bul ") or cmd_lower == "bul":
                    query = command[4:].strip() if cmd_lower.startswith("bul ") else ""
                    if query:
                        from search_bot import web_search_and_summarize
                        ans, sources = web_search_and_summarize(query, system_instruction=system_instruction)
                        if JarvisHTTPHandler.update_last_response_cb:
                            JarvisHTTPHandler.update_last_response_cb(ans)
                        response_text = ans
                        if sources:
                            response_text += "\n\n[Kaynaklar]:\n" + "\n".join([f"- {title}: {uri}" for title, uri in sources])
                        if JarvisHTTPHandler.log_cb:
                            JarvisHTTPHandler.log_cb(f"\n[JARVIS - Mobil Arama]", "system")
                            JarvisHTTPHandler.log_cb(ans)
                    else:
                        response_text = "Ne bulmak istiyorsunuz?"
                else:
                    from search_bot import ask_gemini
                    ans = ask_gemini(command, system_instruction=system_instruction)
                    if JarvisHTTPHandler.update_last_response_cb:
                        JarvisHTTPHandler.update_last_response_cb(ans)
                    response_text = ans
                    if JarvisHTTPHandler.log_cb:
                        JarvisHTTPHandler.log_cb(f"\n[JARVIS - Mobil]", "system")
                        JarvisHTTPHandler.log_cb(ans)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "response": response_text}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/system":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                action = data.get("action", "")
                if JarvisHTTPHandler.execute_system_cmd_cb:
                    JarvisHTTPHandler.execute_system_cmd_cb(action)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": f"Action {action} executed"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/image":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                img_b64 = data.get("image", "")
                prompt = data.get("prompt", "Bu fotoğrafta ne var?").strip()
                role = data.get("role", "Jarvis")
                system_instruction = JarvisHTTPHandler.roles_dict.get(role, None)
                
                if "," in img_b64:
                    header, img_b64 = img_b64.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                else:
                    mime_type = "image/jpeg"
                
                img_bytes = base64.b64decode(img_b64)
                
                from search_bot import ask_gemini
                ans = ask_gemini(prompt, system_instruction=system_instruction, image_data={"mime_type": mime_type, "data": img_bytes})
                if JarvisHTTPHandler.update_last_response_cb:
                    JarvisHTTPHandler.update_last_response_cb(ans)
                
                if JarvisHTTPHandler.log_cb:
                    JarvisHTTPHandler.log_cb(f"\n[JARVIS - Mobil Görsel Analiz]", "system")
                    JarvisHTTPHandler.log_cb(ans)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "response": ans}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/brightness":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                val = data.get("brightness", 70)
                if JarvisHTTPHandler.set_brightness_cb:
                    JarvisHTTPHandler.set_brightness_cb(val)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/power":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                mode = data.get("mode", "balanced")
                if JarvisHTTPHandler.set_power_plan_cb:
                    JarvisHTTPHandler.set_power_plan_cb(mode)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/clipboard":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                text = data.get("text", "")
                if JarvisHTTPHandler.set_clipboard_text_cb:
                    JarvisHTTPHandler.set_clipboard_text_cb(text)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/reminder":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                minutes = float(data.get("minutes", 5))
                message = data.get("message", "Zaman doldu!")
                if JarvisHTTPHandler.add_reminder_cb:
                    JarvisHTTPHandler.add_reminder_cb(minutes, message)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return
        elif path == "/upload":
            filename = query_params.get('filename', [None])[0]
            dest_dir = query_params.get('dest', [None])[0]
            if filename and dest_dir:
                filename = unquote(filename)
                dest_dir = unquote(dest_dir)
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    os.makedirs(dest_dir, exist_ok=True)
                    out_path = os.path.join(dest_dir, filename)
                    with open(out_path, 'wb') as f:
                        f.write(post_data)
                        
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                    return

        self.send_response(404)
        self.end_headers()

def start_http_server(run_cmd_cb, log_cb, roles_dict, get_cpu_cb, get_ram_cb, exec_sys_cb, update_last_response_cb,
                      get_clip_cb, set_clip_cb, get_bright_cb, set_bright_cb, set_power_cb, add_rem_cb):
    # Bind callbacks to handler class
    JarvisHTTPHandler.run_cmd_cb = run_cmd_cb
    JarvisHTTPHandler.log_cb = log_cb
    JarvisHTTPHandler.roles_dict = roles_dict
    JarvisHTTPHandler.get_cpu_usage_cb = get_cpu_cb
    JarvisHTTPHandler.get_ram_usage_cb = get_ram_cb
    JarvisHTTPHandler.execute_system_cmd_cb = exec_sys_cb
    JarvisHTTPHandler.update_last_response_cb = update_last_response_cb
    
    # Premium features callbacks
    JarvisHTTPHandler.get_clipboard_text_cb = get_clip_cb
    JarvisHTTPHandler.set_clipboard_text_cb = set_clip_cb
    JarvisHTTPHandler.get_brightness_cb = get_bright_cb
    JarvisHTTPHandler.set_brightness_cb = set_bright_cb
    JarvisHTTPHandler.set_power_plan_cb = set_power_cb
    JarvisHTTPHandler.add_reminder_cb = add_rem_cb

    server_address = ('0.0.0.0', 5050)
    try:
        httpd = HTTPServer(server_address, JarvisHTTPHandler)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
            
        def log_startup():
            log_cb(f"[SİSTEM] Mobil arayüz aktif: http://{local_ip}:5050", "system")
        
        threading.Timer(1.5, log_startup).start()
        httpd.serve_forever()
    except Exception as e:
        log_cb(f"[HATA] Mobil bağlantı sunucusu başlatılamadı: {str(e)}", "error")
