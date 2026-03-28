import customtkinter as ctk
import speech_recognition as sr
import threading
import time
import re
import tkinter as tk
from config import *
from audio_handler import find_mic_index, transcribe_audio, speak
from ai_brain import get_ai_response_stream
from system_commands import execute_command, search_web, open_url

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI Ayarları
        self.geometry(f"{HUD_WIDTH}x{HUD_HEIGHT}+10+10") # Köşeden biraz içeride
        self.overrideredirect(True) 
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")
        
        # Görev çubuğundan gizleme işlemini pencere oluştuktan sonra yap
        self.after(100, self.hide_from_taskbar)

        self.canvas = tk.Canvas(self, width=HUD_WIDTH, height=HUD_HEIGHT, 
                               bg='black', highlightthickness=0, bd=0)
        self.canvas.pack()

        # ... (HUD Elementleri aynı)
        self.top_left_text = self.canvas.create_text(
            5, 20, text="J.A.R.V.I.S.", anchor="nw",
            fill=COLOR_HUD, font=("Consolas", 18, "bold")
        )
        self.status_dot = self.canvas.create_oval(
            175, 30, 190, 45, 
            fill=COLOR_HUD, outline=COLOR_HUD
        )

        # Durum Değişkenleri
        self.is_processing = False
        self.in_conversation = False
        self.is_speaking = False
        self.interrupted = False
        self.stop_event = threading.Event()
        
        self.mic_index = find_mic_index()
        self.system_print(f"HUD BACKGROUND PROTOCOL ACTIVE.")
        
        # Arka Plan İşlemleri
        self.create_visualizer()
        threading.Thread(target=self.initial_greeting, daemon=True).start()
        threading.Thread(target=self.wake_word_listener, daemon=True).start()
        self.pulse_animation()
        self.update_visualizer()
        
        # 'r' tuşu ile manuel reset/interrupt
        self.bind_all("<r>", self.manual_interrupt)
        self.bind_all("<R>", self.manual_interrupt)

    def hide_from_taskbar(self):
        try:
            import ctypes
            set_window_long = ctypes.windll.user32.SetWindowLongPtrW
            get_window_long = ctypes.windll.user32.GetWindowLongPtrW
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            
            # Ana pencere ID'sini al
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0: hwnd = self.winfo_id()
            
            style = get_window_long(hwnd, GWL_EXSTYLE)
            style |= WS_EX_TOOLWINDOW
            set_window_long(hwnd, GWL_EXSTYLE, style)
            
            # Değişikliği zorla uygula
            self.attributes("-topmost", True)
        except Exception as e:
            log(f"Taskbar hide error: {e}")

    def create_visualizer(self):
        self.bars = []
        bar_count = 12
        bar_width = 4
        gap = 3
        start_x = 35
        for i in range(bar_count):
            x = start_x + i * (bar_width + gap)
            bar = self.canvas.create_rectangle(
                x, 60, x + bar_width, 64,
                fill=COLOR_HUD, outline=""
            )
            self.bars.append(bar)

    def update_visualizer(self):
        import random
        status_color = COLOR_HUD
        
        if self.is_speaking:
            status_color = COLOR_LISTENING
        elif self.is_processing:
            status_color = COLOR_PROCESSING
        elif self.in_conversation:
            status_color = COLOR_LISTENING

        for bar in self.bars:
            height = 2
            if self.is_speaking or self.in_conversation:
                height = random.randint(5, 25)
            elif self.is_processing:
                height = random.randint(3, 12)
            else:
                height = random.randint(1, 3)
            
            x1, _, x2, _ = self.canvas.coords(bar)
            self.canvas.coords(bar, x1, 65 - height, x2, 68)
            self.canvas.itemconfig(bar, fill=status_color)
        
        self.after(80, self.update_visualizer)

    def manual_interrupt(self, event=None):
        if self.in_conversation or self.is_speaking or self.is_processing:
            self.system_print("MANUAL RESET INTERRUPT", is_ai=True)
            self.interrupted = True
            import pygame
            pygame.mixer.music.stop()

    def initial_greeting(self):
        time.sleep(1.5)
        self.jarvis_speak("Sistem çevrimiçi efendim. Arayüz yüklendi. Hitap bekleniyor.")

    def pulse_animation(self):
        status_color = COLOR_HUD
        if self.is_speaking:
            status_color = COLOR_LISTENING
        elif self.is_processing:
            status_color = COLOR_PROCESSING
        elif self.in_conversation:
            status_color = COLOR_LISTENING
        elif not self.is_processing and not self.in_conversation:
            current_color = self.canvas.itemcget(self.status_dot, "fill")
            status_color = "#004455" if current_color == COLOR_HUD else COLOR_HUD
            
        self.canvas.itemconfig(self.status_dot, fill=status_color, outline=status_color)
        self.after(1000, self.pulse_animation)

    def system_print(self, text, is_user=False, is_ai=False):
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[SYS]"
        if is_user: prefix = "[gok2]"; text = text.upper()
        elif is_ai: prefix = "[J.A.R.V.I.S.]"
        print(f"<{timestamp}> {prefix} {text}")

    def jarvis_speak(self, text):
        # URL Kontrolü
        url_match = re.search(r'\[OPEN_URL:\s*(.*?)\]', text)
        clean_text = text
        if url_match:
            open_url(url_match.group(1).strip())
            clean_text = re.sub(r'\[OPEN_URL:\s*.*?\]', '', text).strip()

        if not clean_text: return
        
        self.system_print(clean_text, is_ai=True)
        self.is_speaking = True
        self.interrupted = False
        speak(clean_text, lambda: self.interrupted)
        self.is_speaking = False

    def process_query(self, query):
        self.is_processing = True
        
        # Önce sistem komutlarını kontrol et
        response = execute_command(query)
        if response:
            self.jarvis_speak(response)
        elif any(kw in query for kw in ["ara", "bul", "nedir", "kimdir"]):
            term = search_web(query)
            if term: self.jarvis_speak(f"İnternette {term} araştırılıyor.")
        else:
            # AI Brain'e sor
            current_sentence = ""
            stream = get_ai_response_stream(query)
            if stream:
                for chunk in stream:
                    if self.interrupted: break
                    content = chunk.choices[0].delta.content
                    if content:
                        current_sentence += content
                        if any(p in content for p in [".", "!", "?", "\n"]):
                            clean_sent = current_sentence.strip()
                            if len(clean_sent) > 2:
                                self.jarvis_speak(clean_sent)
                            current_sentence = ""
                if current_sentence.strip() and not self.interrupted:
                    self.jarvis_speak(current_sentence.strip())
        
        self.is_processing = False

    def conversation_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        recognizer.energy_threshold = 5000 # Hassasiyet artırıldı
        
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                while self.in_conversation:
                    try:
                        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                        query = transcribe_audio(audio)
                        
                        # Filtreleme: Gereksiz ve hatalı algılamaları engelle
                        if not query or len(query) < 3: continue
                        junk_phrases = ["m.k.", "altyazı", "altyazi", "teşekkür ederim", "izlediğiniz için"]
                        if any(phrase in query for phrase in junk_phrases) and len(query) < 20:
                            continue
                        
                        self.system_print(query, is_user=True)
                        
                        if any(cmd in query for cmd in ["uyu"]):
                            self.jarvis_speak("Jarvis: Versiyon bir nokta on kapatılıyor. İyi günler efendim.")
                            self.after(1000, self.destroy)
                            return
                        if any(cmd in query for cmd in ["beklemede kal", "bekle", "güle güle"]):
                            self.jarvis_speak("Sistem bekleme moduna alınıyor.")
                            self.in_conversation = False
                            break
                        
                        self.process_query(query)
                    except Exception as e:
                        log(f"Listen Error: {e}")
                        continue
        except Exception as e:
            log(f"Mic Error: {e}")

    def wake_word_listener(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 5000
        while not self.stop_event.is_set():
            if not self.in_conversation and not self.is_processing and not self.is_speaking:
                try:
                    with sr.Microphone(device_index=self.mic_index) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        try:
                            audio = recognizer.listen(source, phrase_time_limit=2.5, timeout=None)
                            text = transcribe_audio(audio)
                            if text and "jarvis" in text:
                                self.jarvis_speak("Buyrun efendim.")
                                self.in_conversation = True
                                threading.Thread(target=self.conversation_loop, daemon=True).start()
                        except: pass
                except: time.sleep(2)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
