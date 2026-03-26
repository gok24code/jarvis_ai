import customtkinter as ctk
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
import os
import threading
import pygame
import tempfile
import time
import re
import webbrowser
import subprocess
import asyncio
import edge_tts
from groq import Groq
from dotenv import load_dotenv
import tkinter as tk

# --- DEBUG AYARI ---
DEBUG = True

def log(message):
    if DEBUG:
        print(f"[SYSTEM_LOG] {message}")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

client_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
client_eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

# Pygame Mixer Hazırlığı
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PROFESYONEL HUD AYARLARI ---
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.overrideredirect(True) 
        
        # ARKA PLANDA TUTMA
        self.attributes("-topmost", False)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        self.lower() 

        # STİL SABİTLERİ (HUD Mavi Tonları)
        self.COLOR_HUD = "#00f3ff"   # Neon Siyan (Sabit Renk)
        self.COLOR_LISTENING = "#007bff"
        self.COLOR_PROCESSING = "#0033ff"

        self.canvas = tk.Canvas(self, width=self.screen_width, height=self.screen_height, 
                               bg='black', highlightthickness=0, bd=0)
        self.canvas.pack()

        # Merkez Koordinatları
        self.cx, self.cy = self.screen_width // 2, self.screen_height // 2
        
        # HUD Grafikleri
        self.base_radius = 120
        self.current_radius = 120
        self.main_circle = self.canvas.create_oval(
            self.cx - self.base_radius, self.cy - self.base_radius,
            self.cx + self.base_radius, self.cy + self.base_radius,
            outline=self.COLOR_HUD, width=4
        )
        
        self.jarvis_text = self.canvas.create_text(
            self.cx, self.cy, text="JARVIS", 
            fill=self.COLOR_HUD, font=("Consolas", 32, "bold")
        )

        # Durum Değişkenleri
        self.is_processing = False
        self.in_conversation = False
        self.is_speaking = False
        self.interrupted = False
        self.stop_event = threading.Event()
        
        self.mic_index = self.find_steelseries_mic()
        self.system_print(f"HUD BACKGROUND PROTOCOL ACTIVE.")
        
        # Arka Plan İşlemleri
        threading.Thread(target=self.initial_greeting, daemon=True).start()
        threading.Thread(target=self.wake_word_listener, daemon=True).start()
        self.pulse_animation()
        self.stay_in_background()
        
        # 'r' tuşu ile manuel reset/interrupt
        self.bind_all("<r>", self.manual_interrupt)
        self.bind_all("<R>", self.manual_interrupt)

    def manual_interrupt(self, event=None):
        """Kullanıcı 'r' tuşuna bastığında konuşmayı ve işlemi keser."""
        if self.in_conversation or self.is_speaking or self.is_processing:
            self.system_print("MANUAL RESET INTERRUPT", is_ai=True)
            self.interrupted = True
            try:
                pygame.mixer.music.stop()
            except: pass

    def stay_in_background(self):
        """Uygulamayı sürekli en arkada tutar."""
        self.lower()
        self.after(2000, self.stay_in_background)

    def initial_greeting(self):
        time.sleep(1.5)
        self.speak("Sistem çevrimiçi efendim. Arayüz yüklendi. Hitap bekleniyor.")

    def find_steelseries_mic(self):
        try:
            mic_list = sr.Microphone.list_microphone_names()
            for index, name in enumerate(mic_list):
                if "steelseries" in name.lower(): return index
            return None
        except: return None

    def pulse_animation(self):
        """Bekleme modunda hafif parlama, konuşurken büyüme efekti"""
        if self.is_speaking:
            # Konuşurken halkayı büyüt
            target_radius = self.base_radius + 30
            self.update_circle_size(target_radius)
        elif not self.is_processing and not self.in_conversation:
            # Bekleme modunda nefes alıp verme
            current_color = self.canvas.itemcget(self.main_circle, "outline")
            target_color = "#004455" if current_color == self.COLOR_HUD else self.COLOR_HUD
            self.canvas.itemconfig(self.main_circle, outline=target_color)
            self.canvas.itemconfig(self.jarvis_text, fill=target_color)
            self.update_circle_size(self.base_radius)
        else:
            self.update_circle_size(self.base_radius)
            
        self.after(1000, self.pulse_animation)

    def update_circle_size(self, radius):
        """Halkanın boyutunu günceller."""
        self.canvas.coords(self.main_circle, 
                           self.cx - radius, self.cy - radius, 
                           self.cx + radius, self.cy + radius)

    def system_print(self, text, is_user=False, is_ai=False):
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[SYS]"
        if is_user: prefix = "[gok2]"; text = text.upper()
        elif is_ai: prefix = "[J.A.R.V.I.S.]"
        print(f"<{timestamp}> {prefix} {text}")

    def speak(self, text):
        # URL Kontrolü (Cevabın içinde [OPEN_URL: ...] varsa aç)
        url_match = re.search(r'\[OPEN_URL:\s*(.*?)\]', text)
        clean_text = text
        if url_match:
            url = url_match.group(1).strip()
            webbrowser.open(url)
            clean_text = re.sub(r'\[OPEN_URL:\s*.*?\]', '', text).strip()

        if not clean_text.strip(): return

        self.system_print(clean_text, is_ai=True)
        self.is_speaking = True
        self.interrupted = False
        
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_path = tmp_file.name

            try:
                if client_eleven:
                    audio_iterator = client_eleven.text_to_speech.convert(
                        text=clean_text,
                        voice_id="pNInz6obpgDQGcFmaJgB",
                        model_id="eleven_multilingual_v2",
                        output_format="mp3_44100_128"
                    )
                    with open(tmp_path, "wb") as f:
                        for chunk in audio_iterator:
                            if chunk: f.write(chunk)
                else: raise Exception()
            except:
                # Ahmet sesini daha ağırbaşlı ve karizmatik (kalın/yavaş) hale getiriyoruz
                communicate = edge_tts.Communicate(clean_text, "tr-TR-AhmetNeural", rate="-5%", pitch="-10Hz")
                asyncio.run(communicate.save(tmp_path))

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                
                # 'r' tuşu ile kesilmeyi kontrol et
                while pygame.mixer.music.get_busy() and not self.interrupted:
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.1)
                try: os.remove(tmp_path)
                except: pass
        except Exception as e:
            self.system_print(f"AUDIO_ERR: {e}")
            
        self.is_speaking = False

    def process_and_speak_stream(self, query):
        self.is_processing = True
        current_sentence = ""
        try:
            stream = client_groq.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Adın Jarvis. Karizmatik, ağırbaşlı, mütvazi ve son derece zeki bir yapay zekasın. Cevapların kısa, öz ve bir beyefendi (gentleman) tarzında olsun. Türkçe konuşuyorsun. Web araması veya site açma isteklerinde cevabının en sonuna [KAYNAKÇA: <url>] ekle."},
                    {"role": "user", "content": query}
                ],
                model="llama-3.3-70b-versatile",
                stream=True,
            )
            for chunk in stream:
                if self.interrupted: break
                content = chunk.choices[0].delta.content
                if content:
                    current_sentence += content
                    if any(p in content for p in [".", "!", "?", "\n"]):
                        clean_sent = current_sentence.strip()
                        if len(clean_sent) > 2:
                            self.speak(clean_sent)
                        current_sentence = ""
            if current_sentence.strip() and not self.interrupted:
                self.speak(current_sentence.strip())
        except Exception as e:
            self.system_print(f"STREAM_ERR: {e}")
        self.is_processing = False

    def conversation_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        recognizer.energy_threshold = 4000  # Klavye ve çevre seslerini filtrelemek için yükseltildi
        
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                while self.in_conversation:
                    try:
                        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                        query = self.transcribe_audio(audio)
                        
                        if not query or len(query) < 3: continue
                        if query in ["m.k.", "m.k", "mk", "altyazı", "ALTYAZI M.K.", "M.K.","ALTYAZI","M.","K.", "teşekkür ederim"]: continue
                        
                        self.system_print(query, is_user=True)
                    except Exception as e:
                        log(f"Listen Error: {e}")
                        continue

                    if any(cmd in query for cmd in ["programı kapat", "uygulamayı kapat", "sistemi kapat"]):
                        self.speak("Sistem kapatılıyor. İyi günler efendim.")
                        self.after(1000, self.destroy)
                        return

                    if any(cmd in query for cmd in ["beklemede kal", "bekle", "güle güle"]):
                        self.speak("Sistem bekleme moduna alınıyor.")
                        self.in_conversation = False
                        break
                    
                    # --- WEB VE YEREL KOMUTLAR ---
                    target_dir = r"C:/Users/gok2/Desktop/git"
                    discord_exe = r"C:\Users\gok2\AppData\Local\Discord\Update.exe"
                    
                    if any(kw in query for kw in ["ara", "bul", "nedir", "kimdir"]):
                        search_term = query.replace("ara", "").replace("bul", "").replace("internette", "").strip()
                        if search_term:
                            url = f"https://duckduckgo.com/?q={search_term}"
                            self.speak(f"İnternette {search_term} araştırılıyor.")
                            webbrowser.open(url)
                            continue

                    sites = {"youtube": "https://www.youtube.com", "gitab": "https://github.com/gok24code?tab=repositories", "versel": "https://vercel.com", "websitem": "https://prometh-labs.vercell.app"}
                    found_site = False
                    for site, url in sites.items():
                        if site in query and ("aç" in query or "git" in query):
                            self.speak(f"{site.capitalize()} açılıyor efendim.")
                            webbrowser.open(url); found_site = True; break
                    if found_site: continue

                    if "discord" in query and "aç" in query:
                        self.speak("Discord açılıyor efendim.")
                        # Access Denied hatasını önlemek için shell=True ve start komutu kullanıyoruz
                        cmd = f'start "" "{discord_exe}" --processStart Discord.exe'
                        subprocess.Popen(cmd, shell=True)
                        continue

                    if "gemini" in query and "terminal" in query:
                        self.speak("Gemini başlatılıyor."); os.system(f'start cmd /k "cd /d {target_dir} && gemini"'); continue
                    if "editör" in query:
                        self.speak("Editör açılıyor."); subprocess.Popen(["code", target_dir], shell=True); continue
                    if "terminal" in query:
                        self.speak("Terminal açılıyor."); subprocess.Popen(["wt.exe", "-d", target_dir], shell=True); continue

                    self.process_and_speak_stream(query)
        except Exception as e:
            log(f"Mic Error: {e}")
            
    def transcribe_audio(self, audio_data):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                tmp_audio.write(audio_data.get_wav_data())
                tmp_audio_path = tmp_audio.name
            with open(tmp_audio_path, "rb") as file:
                transcription = client_groq.audio.transcriptions.create(
                    file=(tmp_audio_path, file.read()),
                    model="whisper-large-v3-turbo",
                    language="tr", response_format="text"
                )
            if os.path.exists(tmp_audio_path): os.remove(tmp_audio_path)
            return transcription.strip().lower()
        except: return None

    def wake_word_listener(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 5000 # Bekleme modunda daha yüksek eşik
        while not self.stop_event.is_set():
            if not self.in_conversation and not self.is_processing and not self.is_speaking:
                try:
                    with sr.Microphone(device_index=self.mic_index) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        try:
                            audio = recognizer.listen(source, phrase_time_limit=2.5, timeout=None)
                            text = self.transcribe_audio(audio)
                            if text and "jarvis" in text:
                                self.speak("Buyrun efendim.")
                                self.in_conversation = True
                                self.after(0, lambda: threading.Thread(target=self.conversation_loop, daemon=True).start())
                        except: pass
                except: time.sleep(2)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
