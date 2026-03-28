# J.A.R.V.I.S. - Yapay Zeka Asistanı

J.A.R.V.I.S. (Just A Rather Very Intelligent System), Iron Man'den esinlenilerek geliştirilmiş, sesli komutlarla çalışan, fütüristik bir HUD arayüzüne sahip gelişmiş bir masaüstü asistanıdır.

## 🚀 Özellikler

- **Sesli Aktivasyon:** "Jarvis" uyandırma kelimesi ile tetikleme.
- **Gelişmiş Zeka:** Groq üzerinden **Llama 3.3 70B Versatile** modeli ile akıcı ve karakter sahibi sohbetler.
- **Yüksek Kaliteli Ses:** **ElevenLabs** (V2 Multilingual) ile doğal seslendirme, internet olmadığında **Edge-TTS** (AhmetNeural) ile otomatik yedekleme.
- **Anlık Transkripsiyon:** **Whisper-large-v3-turbo** ile düşük gecikmeli ses algılama.
- **Gemini CLI Entegrasyonu:** Sesli komutla yeni proje klasörleri oluşturma ve Gemini'ye detaylı teknik talimatlar ileterek geliştirme sürecini başlatma.
- **Sistem Entegrasyonu:**
  - **Uygulama Kontrolü:** Discord, Spotify (Play/Pause desteği), Blender (+ Hologram Modu), VS Code ve Windows Terminal başlatma.
  - **Web Navigasyonu:** YouTube, GitHub, Vercel ve Prometh Labs gibi platformlara hızlı erişim.
  - **Arama:** DuckDuckGo üzerinden internet araştırması yapabilme.
  - **Sistem Komutları:** Bilgisayar kilitleme ve disk temizleme aracı çalıştırma.
- **Fütüristik HUD:** Ekranın üst köşesinde yer alan, işlem durumuna (Dinleme, İşleme, Konuşma) göre renk değiştiren ve canlı ses görselleştiricisi (visualizer) içeren şeffaf arayüz.
- **Akıllı Kesme (Interrupt):** 'R' tuşu ile asistanın konuşmasını anında durdurma veya sistemi manuel olarak resetleme.

## 🛠️ Teknoloji Yığını

- **Dil:** Python 3.x
- **Yapay Zeka:** Groq Cloud API (LLM & STT)
- **Ses Sentezi:** ElevenLabs API & Microsoft Edge-TTS
- **Arayüz:** CustomTkinter & Tkinter (Canvas-based Visualizer)
- **Ses İşleme:** SpeechRecognition, Pygame (Mixer), Pyaudio

## 📋 Gereksinimler

Proje için gerekli kütüphaneleri yüklemek için:

```bash
pip install -r requirements.txt
```

_Not: `pyaudio` yüklemesi sırasında sorun yaşarsanız, Windows için uygun `.whl` dosyasını kullanmanız gerekebilir._

## ⚙️ Kurulum ve Yapılandırma

1. Proje ana dizinine bir `.env` dosyası oluşturun ve API anahtarlarınızı ekleyin:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```
2. `config.py` dosyasındaki dosya yollarını (`DISCORD_PATH`, `SPOTIFY_PATH`, `BLENDER_PATH`, `TARGET_DIR`) kendi sisteminize göre güncelleyin.
3. Uygulamayı başlatın:
   ```bash
   python jarvis_ui.pyw
   ```

## 📂 Dosya Yapısı

- `jarvis_ui.pyw`: HUD arayüz yönetimi, görselleştirici animasyonları ve ana uygulama döngüsü.
- `ai_brain.py`: Groq API entegrasyonu, karakter tanımlamaları ve Gemini prompt oluşturma mantığı.
- `audio_handler.py`: Ses algılama (STT) ve çift katmanlı seslendirme (TTS) yönetimi.
- `system_commands.py`: Uygulama başlatma, web aramaları ve Gemini CLI otomasyonu.
- `config.py`: Renk paleti, API istemcileri ve sistem yolları gibi merkezi ayarlar.

## ⌨️ Kısayollar ve Kontrol

- **"Jarvis"**: Sistemi dinleme moduna geçirir.
- **'R' Tuşu**: Konuşmayı o anda keser ve sistemi bekleme moduna resetler.
- **"Gemini [Proje Tanımı] yap/aç"**: Belirtilen proje için klasör oluşturur ve Gemini'yi teknik talimatlarla başlatır.
- **"Beklemede Kal / Güle Güle"**: Aktif konuşmayı bitirir ancak arka planda dinlemeye devam eder.
- **"Sistemi Kapat"**: Uygulamayı tamamen sonlandırır.

---

## branchlerden en günceli main branchidir.

_Geliştiren: [gok24code](https://github.com/gok24code)_
