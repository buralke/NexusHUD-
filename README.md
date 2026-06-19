# NexusHUD: Local AI Assistant & System Controller

NexusHUD, bilgisayarınızı yerel ağ (Wi-Fi) ve Telegram üzerinden kontrol etmenizi sağlayan, Gemini API destekli, siberpunk estetiğine sahip modern bir masaüstü asistanı ve uzaktan yönetim merkezidir.

Masaüstünde şık bir **PySide6 (Qt6)** arayüzü sunarken, arka planda çalışan web sunucusu ve Telegram botu sayesinde bilgisayarınızı dilediğiniz yerden güvenle yönetmenize imkan tanır.

---

## 🚀 Özellikler

### 🖥 Masaüstü Arayüzü (PySide6 / Qt6)
- **Siberpunk Neon Tasarımı:** Yüksek kontrastlı, koyu arka plan (`#060913`) ve neon-cyan (`#00f3ff`) renkleriyle tasarlanmış endüstriyel HUD tasarımı.
- **Kullanım Kolaylığı:** İlk açılışta otomatik beliren **Kurulum Kılavuzu** sayesinde Gemini API ve Telegram Bot kurulumunu adım adım linkleriyle birlikte gösterir.
- **Yapay Zeka & Arama:** Gemini API üzerinden farklı sistem rolleriyle sohbet edebilir veya Wikipedia aramaları yapabilirsiniz.
- **Yerel Kısayollar:** `command.json` dosyasına tanımlayacağınız kelimelerle programları, web sitelerini veya dosyaları arayüzdeki butonlar veya terminalden anında açabilirsiniz.
- **Sistem Kontrolleri:** Ses düzeyini (Sessiz/Oynat/Ses -/Ses +) yönetebilir, bilgisayarı kilitleyebilir veya uyku moduna alabilirsiniz.
- **Donanım Metrikleri:** CPU ve RAM yük durumunu canlı metrik grafikleriyle takip edebilirsiniz.
- **Görsel Analiz:** Bilgisayarınızdan seçeceğiniz herhangi bir görseli Gemini API'ye gönderip analiz ettirebilirsiniz.

### 🤖 Telegram Uzaktan Kontrol & PIN Güvenliği
- **Kalıcı Statik PIN:** Bot erişimi `.env` dosyasında saklanan kalıcı bir şifre (PIN) ile korunur. İlk mesaj atan kullanıcılardan bu PIN istenir ve doğru girildiğinde kullanıcı ID'si `.env` dosyasına kaydedilerek yetkilendirilir.
- **Dinamik Güncelleme:** Şifreyi masaüstü arayüzündeki **[Telegram Ayarları]** panelinden veya yetkili bir hesaptan `/setpin <yeni_şifre>` yazarak anında güncelleyebilirsiniz (yeniden başlatma gerektirmez).
- **Zengin Komut Kütüphanesi:**
  - `/stats` - Canlı CPU & RAM durumunu gösterir.
  - `/screen` - Bilgisayarın anlık ekran görüntüsünü alıp Telegram'dan gönderir.
  - `/cam` - PC kamerasından fotoğraf çekip gönderir.
  - `/notifications` - Bilgisayara gelen son Windows bildirimlerini okur.
  - `/clip` / `/setclip <metin>` - Panoyu okur veya yazar.
  - `/ls` - Etkileşimli dosya yöneticisini açarak dosyaları indirmenizi sağlar.
  - `/cmd <komut>` - Uzaktan Windows CMD komutları çalıştırır.
  - `/shutdown` / `/restart` - Onay butonlu bilgisayar kapatma/yeniden başlatma.

### ⏰ Gelişmiş Zamanlanmış ve Tekrarlı Hatırlatıcılar
- **Tekrarlı Hatırlatıcılar:** Belirli aralıklarla (örn. her 30 dakikada bir "Su iç") çalışan hatırlatıcılar kurabilirsiniz.
- **Zamanlanmış Hatırlatıcılar:** Belirli bir tarih ve saatte (örn. "22.06.2026 14:00 Hastane randevusu") çalışacak hatırlatıcılar kurabilirsiniz.
- **Nagging (Tekrarlayan Bildirim):** Zamanlanmış bir hatırlatıcı geldiğinde siz onu kapatana kadar belirlediğiniz sıklıkta (örn. her 15 dakikada bir) sizi uyarmaya devam eder.
- **Çift Yönlü Bildirim:** Süre dolduğunda masaüstünde sesli ve görsel bir popup penceresi açılırken, aynı anda Telegram botu üzerinden izinli kullanıcılara kapatma/silme butonlu bildirim mesajı gönderilir.

---

## 🛠 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleyin
Uygulamanın çalışması için gerekli kütüphaneleri yükleyin:
```bash
pip install PySide6 python-dotenv google-generativeai requests opencv-python
```

### 2. Şablon Yapılandırması
Proje dizininde yer alan `.env.example` dosyasını kopyalayarak `.env` adında bir dosya oluşturun ve değerleri tanımlayın:
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USER_IDS=
TELEGRAM_AUTH_PIN=123456
```
*(Eğer bu değerleri boş bırakırsanız, uygulama ilk açıldığında size rehberlik eden kurulum kılavuzunu gösterecektir. Değerleri arayüz içerisindeki ayarlardan da kolayca kaydedebilirsiniz.)*

### 3. Çalıştırma
Uygulamayı başlatmak için terminalden ana dosyayı çalıştırmanız yeterlidir:
```bash
python ui.py
```

---

## 🎨 Tasarım Estetiği
Arayüz, modern Qt6 (PySide6) standartlarına uygun olarak tasarlanmış siberpunk temalı koyu gri ve neon camgöbeği renk paletine sahiptir. Pencere kenarları, düğmeler, metin girişleri ve kaydırıcılar modern masaüstü uygulamalarıyla uyumlu şekilde tamamen flat/düzleştirilmiş stil şablonları (QSS) ile özelleştirilmiştir.
