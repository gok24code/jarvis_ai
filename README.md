# J.A.R.V.I.S. - Yapay Zeka Asistanı

J.A.R.V.I.S. (Just A Rather Very Intelligent System), Iron Man'den esinlenilerek geliştirilmiş, sesli komutlarla çalışan, şık bir HUD arayüzüne sahip gelişmiş bir masaüstü asistanıdır.

## 🚀 Özellikler

- **Sesli Aktivasyon:** "Jarvis" uyandırma kelimesi ile tetikleme.
- **Gelişmiş Zeka:** Groq üzerinden **Llama 3.3 70B** modeli ile akıcı ve karakter sahibi sohbetler.
- **Yüksek Kaliteli Ses:** **ElevenLabs** (V2 Multilingual) ile doğal seslendirme, internet olmadığında **Edge-TTS** ile otomatik yedekleme.
- **Anlık Transkripsiyon:** **Whisper-large-v3-turbo** ile düşük gecikmeli ses algılama.
- **Sistem Entegrasyonu:**
  - Uygulama başlatma (Discord, VS Code, Terminal vb.).
  - Web araması (DuckDuckGo üzerinden).
  - Bilgisayar kilitleme, temizlik aracı çalıştırma gibi sistem komutları.
- **Fütüristik HUD:** Ekranın üst köşesinde yer alan, işlem durumuna göre renk değiştiren şeffaf arayüz.
- **Manuel Müdahale:** 'R' tuşu ile asistanı durdurma veya konuşmayı kesme.

## 🛠️ Teknoloji Yığını

- **Dil:** Python
- **Yapay Zeka:** Groq API (LLM & STT)
- **Ses Sentezi:** ElevenLabs & Edge-TTS
- **Arayüz:** CustomTkinter & Tkinter
- **Ses İşleme:** SpeechRecognition, Pygame (Mixer), Pyaudio

## 📋 Gereksinimler

Proje için gerekli kütüphaneleri yüklemek için:

```bash
pip install -r requirements.txt
```

*Not: `pyaudio` yüklemesi sırasında sorun yaşarsanız, Windows için uygun `.whl` dosyasını kullanmanız gerekebilir.*

## ⚙️ Kurulum ve Yapılandırma

1. Proje ana dizinine bir `.env` dosyası oluşturun ve API anahtarlarınızı ekleyin:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```
2. `config.py` dosyasındaki dosya yollarını (Örn: `DISCORD_PATH`, `TARGET_DIR`) kendi sisteminize göre güncelleyin.
3. Uygulamayı başlatın:
   ```bash
   python jarvis_ui.pyw
   ```

## 📂 Dosya Yapısı

- `jarvis_ui.pyw`: Ana uygulama döngüsü ve HUD arayüz yönetimi.
- `ai_brain.py`: Groq API entegrasyonu ve karakter tanımlamaları.
- `audio_handler.py`: Ses algılama (STT) ve seslendirme (TTS) mantığı.
- `system_commands.py`: Web aramaları ve sistem komutlarının yürütülmesi.
- `config.py`: Renk paleti, API istemcileri ve sistem yolları gibi sabitler.

## ⌨️ Kısayollar ve Kontrol

- **"Jarvis"**: Sistemi dinleme moduna geçirir.
- **'R' Tuşu**: Konuşmayı o anda keser ve sistemi bekleme moduna resetler.
- **"Sistemi Kapat"**: Uygulamayı sonlandırır.
- **"Beklemede Kal / Güle Güle"**: Aktif konuşmayı bitirir ancak arka planda dinlemeye devam eder.

---
*Geliştiren: [gok24code](https://github.com/gok24code)*
