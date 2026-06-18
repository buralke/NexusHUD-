# NexusHUD: Local AI Assistant & System Controller

NexusHUD, bilgisayarınızı yerel ağ (Wi-Fi) üzerinden kontrol etmenizi sağlayan, Gemini API destekli ve cyberpunk estetiğine sahip hafif (lightweight) bir masaüstü asistanı ve mobil kontrol merkezidir.

Masaüstünde şık bir Python Tkinter arayüzü sunarken, arka planda çalışan hafif HTTP sunucusu sayesinde aynı ağa bağlı telefon veya tabletinizden bilgisayarınızı uzaktan yönetmenize imkan tanır.

---

## 🚀 Özellikler

### 🖥 Masaüstü Arayüzü (Python & Tkinter)
- **Yapay Zeka & Arama:** Gemini API üzerinden farklı sistem rolleriyle sohbet edebilir veya Wikipedia aramaları yapabilirsiniz.
- **Yerel Kısayollar:** `command.json` dosyasına tanımlayacağınız kelimelerle programları, web sitelerini veya dosyaları anında açabilirsiniz.
- **İsteğe Bağlı Sesli Yanıt (TTS):** Gelen cevapları istediğiniz an tek tıkla Windows'un yerel PowerShell ses motoru üzerinden Türkçe olarak dinleyebilirsiniz.
- **Sistem Kontrolleri:** Ses seviyesini ayarlayabilir (Arttır/Azalt/Sessiz), medyayı duraklatıp oynatabilir, bilgisayarı kilitleyebilir veya uyku moduna alabilirsiniz.
- **Canlı Metrikler:** CPU ve RAM yük durumunu anlık (3 saniyede bir) olarak grafiksel metriklerle takip edebilirsiniz.
- **Görsel Analiz:** Bilgisayarınızdan seçeceğiniz herhangi bir görseli Gemini API'ye gönderip analiz ettirebilirsiniz.

### 📱 Mobil Web Kontrol Merkezi (H.U.D.)
Aynı Wi-Fi ağına bağlı herhangi bir mobil cihazın tarayıcısından bilgisayarınızdaki sunucuya bağlanarak şu özellikleri kullanabilirsiniz:
- **Yapay Zeka Sohbeti & Sesli Tanıma:** Telefona sesli konuşarak veya yazarak bilgisayara komut/soru gönderebilir, gelen cevabı telefonunuzun kendi ses motoru ile manuel olarak seslendirebilirsiniz.
- **Uzaktan Kumanda:** Telefonunuzu bir kumanda gibi kullanarak bilgisayarın sesini yönetebilir, medyayı kontrol edebilir veya bilgisayarı uzaktan kilitleyip uyku moduna alabilirsiniz.
- **Kamera & Görsel Analiz:** Telefonunuzla o an çektiğiniz bir fotoğrafı doğrudan bilgisayarınızdaki yapay zekaya analiz ettirebilirsiniz.
- **Mobil Metrik Takibi:** Bilgisayarınızın CPU ve RAM durumunu telefonunuzun ekranından canlı izleyebilirsiniz.

---

## 🛠 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleyin
Proje harici kütüphane bağımlılığı olmadan çalışacak şekilde tasarlanmıştır. Sadece Gemini API kullanmak için gerekli olan resmi paketi ve ortam değişkenleri için dotenv modülünü yüklemeniz yeterlidir:
```bash
pip install google-generativeai python-dotenv
```

### 2. Yapılandırma Dosyaları
Proje dizininde aşağıdaki yapılandırmaların yer aldığından emin olun:

- **`.env`**: Gemini API anahtarınızı tanımlayın (Arayüz içerisinden de girilebilir):
  ```env
  GEMINI_API_KEY=YOUR_GEMINI_API_KEY
  ```
- **`command.json`**: Kısayollarınızı ve bunlara karşılık gelen web linklerini veya dosya yollarını özelleştirin.
- **`roles.json`**: Yapay zekaya atamak istediğiniz farklı sistem talimatlarını (Rolleri) bu dosyadan yönetebilirsiniz.

### 3. Çalıştırma
Uygulamayı başlatmak için terminalden ana dosyayı çalıştırmanız yeterlidir:
```bash
python ui.py
```
*Uygulama başladığında, konsol ekranında telefonunuzdan bağlanabileceğiniz yerel IP adresini (Örn: `http://192.168.1.50:5050`) otomatik olarak gösterecektir.*

---

## 🎨 Tasarım Estetiği
Arayüz, koyu arka plan üzerine yerleştirilmiş canlı mavi (Cyan) ve neon yeşil tonlarıyla modern bir "cyberpunk/terminal" havasına sahiptir. Sistem performansı veya kaynak tüketimi yaratmayacak şekilde Tkinter'ın yerel widget'ları optimize edilerek tasarlanmıştır.
