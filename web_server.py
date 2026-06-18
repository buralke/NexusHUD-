import json
import socket
import base64
import threading
from urllib.parse import quote
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

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Kontrol Merkezi</title>
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
        input[type="text"], select {
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
        input[type="text"]:focus, select:focus {
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
    </style>
</head>
<body>
    <div class="container">
        <h1>JARVIS H.U.D.</h1>
        
        <!-- PC Durumu -->
        <div class="card">
            <div class="card-title">// Sistem Metrikleri</div>
            <div class="stats-grid">
                <div class="stat-box">
                    <div>CPU YÜKÜ</div>
                    <div id="cpu-val" class="stat-val">--%</div>
                </div>
                <div class="stat-box">
                    <div>RAM KULLANIMI</div>
                    <div id="ram-val" class="stat-val">--%</div>
                </div>
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

        function speakLastImgResponse() {
            if (lastImgResponseText) {
                speak(lastImgResponseText);
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
        elif self.path == "/stats":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            stats = {
                "cpu": JarvisHTTPHandler.get_cpu_usage_cb() if JarvisHTTPHandler.get_cpu_usage_cb else 0,
                "ram": JarvisHTTPHandler.get_ram_usage_cb() if JarvisHTTPHandler.get_ram_usage_cb else 0
            }
            self.wfile.write(json.dumps(stats).encode('utf-8'))
            return
        elif self.path == "/roles":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(list(JarvisHTTPHandler.roles_dict.keys())).encode('utf-8'))
            return
            
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/command":
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
        elif self.path == "/system":
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
        elif self.path == "/image":
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

        self.send_response(404)
        self.end_headers()

def start_http_server(run_cmd_cb, log_cb, roles_dict, get_cpu_cb, get_ram_cb, exec_sys_cb, update_last_response_cb):
    # Bind callbacks to handler class
    JarvisHTTPHandler.run_cmd_cb = run_cmd_cb
    JarvisHTTPHandler.log_cb = log_cb
    JarvisHTTPHandler.roles_dict = roles_dict
    JarvisHTTPHandler.get_cpu_usage_cb = get_cpu_cb
    JarvisHTTPHandler.get_ram_usage_cb = get_ram_cb
    JarvisHTTPHandler.execute_system_cmd_cb = exec_sys_cb
    JarvisHTTPHandler.update_last_response_cb = update_last_response_cb

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
        
        # We assume the caller starts this inside a thread, so we run log_startup directly via a timer or after root is ready
        threading.Timer(1.5, log_startup).start()
        httpd.serve_forever()
    except Exception as e:
        log_cb(f"[HATA] Mobil bağlantı sunucusu başlatılamadı: {str(e)}", "error")
