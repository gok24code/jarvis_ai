import customtkinter as ctk
import speech_recognition as sr
import threading
import time
import re
import tkinter as tk
import os
import asyncio
import tempfile
from PIL import Image, ImageTk, ImageSequence
from config import *
from audio_handler import find_mic_index, transcribe_audio, speak, speak_edge_tts
import ai_brain
from ai_brain import get_ai_response_stream
from system_commands import execute_command, search_web, open_url
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
from system_commands import execute_command, search_web, open_url, volume_manager

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.load_env_vars()

        # UI Ayarları (Tam Ekran)
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        
        self.overrideredirect(True) 
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")

        self.after(100, self.apply_window_styles)

        self.canvas = tk.Canvas(self, width=self.screen_width, height=self.screen_height, 
                               bg='black', highlightthickness=0, bd=0)
        self.canvas.pack()

        # Mekanik HUD Ayarları
        self.center_x = self.screen_width // 2 -235
        self.center_y = self.screen_height // 2
        self.angle = 0
        self.pulse_val = 0
        
        # HUD Katman Parçaları (ID listesi)
        self.hud_elements = []
        
        # 1. Dış Kesikli Statik Halka (Derece Göstergesi gibi)
        self.hud_elements.append(self.canvas.create_oval(
            self.center_x-200, self.center_y-200, self.center_x+200, self.center_y+200,
            outline="#002233", width=1, dash=(2, 10)
        ))
        
        # 2. Dönen Segmentler (Arcs)
        self.arc1 = self.canvas.create_arc(0,0,0,0, outline=COLOR_HUD, width=3, style="arc", start=0, extent=60)
        self.arc2 = self.canvas.create_arc(0,0,0,0, outline=COLOR_HUD, width=3, style="arc", start=180, extent=60)
        
        # 3. Orta Kesikli Halka (Ters Dönüş)
        self.mid_ring = self.canvas.create_oval(0,0,0,0, outline=COLOR_HUD, width=1, dash=(10, 20))
        
        # 4. İç Core (Altıgenimsi yapı simülasyonu için 2 arc)
        self.core_arc1 = self.canvas.create_arc(0,0,0,0, outline=COLOR_LISTENING, width=5, style="arc", start=0, extent=120)
        self.core_arc2 = self.canvas.create_arc(0,0,0,0, outline=COLOR_LISTENING, width=5, style="arc", start=180, extent=120)

        self.center_text = self.canvas.create_text(
            self.center_x, self.center_y, text="J.A.R.V.I.S.",
            fill=COLOR_HUD, font=("Consolas", 10, "bold")
        )

        # Sağ Tık Menüsü (Ses Kontrolü için)
        self.menu = tk.Menu(self, tearoff=0, bg="black", fg=COLOR_HUD, activebackground=COLOR_HUD, activeforeground="black")
        self.menu.add_command(label="Ses %100", command=lambda: volume_manager.set_volume(100))
        self.menu.add_command(label="Ses %70", command=lambda: volume_manager.set_volume(70))
        self.menu.add_command(label="Ses %50", command=lambda: volume_manager.set_volume(50))
        self.menu.add_command(label="Ses %30", command=lambda: volume_manager.set_volume(30))
        self.menu.add_command(label="Sessiz", command=lambda: volume_manager.set_volume(0))
        self.menu.add_separator()
        self.menu.add_command(label="Çıkış", command=self.destroy)

        self.bind("<Button-3>", self.show_menu)

        # Durum Değişkenleri
        self.whatsapp_state = None
        self.temp_recipient = None
        
        # Telegram State Tracking
        self.telegram_states = {} # {user_id: {'state': None, 'recipient': None}}

        self.is_processing = False
        self.in_conversation = False
        self.is_speaking = False
        self.interrupted = False
        self.stop_event = threading.Event()
        
        self.mic_index = find_mic_index()
        self.system_print(f"HUD BACKGROUND PROTOCOL ACTIVE.")
        
        # Arka Plan İşlemleri
        threading.Thread(target=self.initial_greeting, daemon=True).start()
        threading.Thread(target=self.wake_word_listener, daemon=True).start()
        
        # TELEGRAM PROTOKOLÜ
        if self.telegram_token:
            threading.Thread(target=self.start_telegram_loop, daemon=True).start()
            self.system_print("TELEGRAM REMOTE ACCESS PROTOCOL ONLINE.")

        self.animate_hud()
        
        self.bind_all("<r>", self.manual_interrupt)
        self.bind_all("<R>", self.manual_interrupt)

    def animate_hud(self):
        import math
        # Duruma göre hız ve renk
        speed_mult = 1.0
        color = COLOR_HUD
        
        if self.is_speaking or self.in_conversation:
            speed_mult = 4.0
            color = COLOR_LISTENING
        elif self.is_processing:
            speed_mult = 2.0
            color = COLOR_PROCESSING

        self.angle += 0.05 * speed_mult
        self.pulse_val += 0.1 * speed_mult
        pulse_scale = 1.0 + (math.sin(self.pulse_val) * 0.05)
        
        cx, cy = self.center_x, self.center_y
        
        # 1. Dış Arcları Döndür (Zıt Yönler)
        r1 = 160 * pulse_scale
        self.canvas.coords(self.arc1, cx-r1, cy-r1, cx+r1, cy+r1)
        self.canvas.itemconfig(self.arc1, start=self.angle*50, outline=color)
        
        self.canvas.coords(self.arc2, cx-r1, cy-r1, cx+r1, cy+r1)
        self.canvas.itemconfig(self.arc2, start=self.angle*50 + 180, outline=color)
        
        # 2. Orta Halka (Ters Dönüş hissi için dash offset simülasyonu olmasa da boyut değişimi)
        r2 = 130 * pulse_scale
        self.canvas.coords(self.mid_ring, cx-r2, cy-r2, cx+r2, cy+r2)
        self.canvas.itemconfig(self.mid_ring, outline=color)
        
        # 3. Core Arcları (Hızlı Dönüş)
        r3 = 60 * (1.0 + math.sin(self.pulse_val*2)*0.1)
        self.canvas.coords(self.core_arc1, cx-r3, cy-r3, cx+r3, cy+r3)
        self.canvas.itemconfig(self.core_arc1, start=-self.angle*80, outline=color)
        
        self.canvas.coords(self.core_arc2, cx-r3, cy-r3, cx+r3, cy+r3)
        self.canvas.itemconfig(self.core_arc2, start=-self.angle*80 + 180, outline=color)
        
        self.canvas.itemconfig(self.center_text, fill=color)

        self.after(30, self.animate_hud)

    def load_env_vars(self):
        load_dotenv()
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        auth_id_raw = os.getenv("AUTHORIZED_USER_ID")
        if auth_id_raw:
            auth_id_raw = auth_id_raw.strip().replace('"', '').replace("'", "")
        try:
            self.auth_user_id = int(auth_id_raw) if auth_id_raw and auth_id_raw.lower() != "none" else None
        except:
            self.auth_user_id = None

    def start_telegram_loop(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            application = Application.builder().token(self.telegram_token).build()
            application.add_handler(MessageHandler(filters.VOICE, self.handle_telegram_query))
            application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_telegram_query))
            
            application.run_polling(close_loop=False)
        except Exception as e:
            log(f"Telegram Loop Error: {e}")

    async def handle_telegram_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.auth_user_id and update.effective_user.id != self.auth_user_id:
            return

        user_id = update.effective_user.id
        if user_id not in self.telegram_states:
            self.telegram_states[user_id] = {"state": None, "recipient": None}

        query_text = ""
        try:
            if update.message.voice:
                voice_file = await update.message.voice.get_file()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as ogg_file:
                    await voice_file.download_to_drive(ogg_file.name)
                    ogg_path = ogg_file.name
                
                wav_path = ogg_path.replace(".ogg", ".wav")
                AudioSegment.from_file(ogg_path).export(wav_path, format="wav")
                
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio_data = recognizer.record(source)
                    query_text = transcribe_audio(audio_data)
                
                if os.path.exists(ogg_path): os.remove(ogg_path)
                if os.path.exists(wav_path): os.remove(wav_path)
            else:
                query_text = update.message.text

            if query_text:
                self.system_print(f"TELEGRAM: {query_text}", is_user=True)
                self.is_processing = True
                
                response_text = ""
                
                # Telegram WhatsApp Flow
                state_data = self.telegram_states[user_id]
                
                if state_data["state"] == "waiting_recipient":
                    # Name extraction with suffix removal
                    clean_name = re.sub(r'(y[ea]|[ea])$', '', query_text.lower().strip())
                    state_data["recipient"] = clean_name
                    state_data["state"] = "waiting_message"
                    response_text = "Mesaj içeriği nedir?"
                
                elif state_data["state"] == "waiting_message":
                    from ai_brain import send_whatsapp_message
                    recipient = state_data["recipient"]
                    message_text = query_text

                    # Mevcut event loop'u al
                    loop = asyncio.get_running_loop()

                    # Telegram'ı kilitlememek için ayrı bir thread'de gönder
                    def bg_send():
                        success = send_whatsapp_message(recipient, message_text)
                        text = f"Anlaşıldı efendim, {recipient} kişisine mesaj iletildi." if success else "Üzgünüm efendim, mesaj gönderilemedi."
                        # Mesajı asıl loop üzerinden geri gönder
                        asyncio.run_coroutine_threadsafe(update.message.reply_text(text), loop)

                    threading.Thread(target=bg_send, daemon=True).start()
                    response_text = f"{recipient} kişisine mesajınız iletiliyor, efendim."

                    state_data["state"] = None
                    state_data["recipient"] = None


                elif any(kw in query_text.lower() for kw in ["mesaj gönder", "mesaj at", "whatsapp"]):
                    # Try to see if recipient is already in this first message
                    # e.g., "Ali'ye mesaj gönder"
                    match = re.search(r'(.*?)([\'"]?[ye]?[ea])?\s+(mesaj gönder|mesaj at|whatsapp)', query_text.lower())
                    if match and match.group(1).strip():
                        recipient = match.group(1).strip()
                        # Clean suffix
                        recipient = re.sub(r'(y[ea]|[ea])$', '', recipient)
                        state_data["recipient"] = recipient
                        state_data["state"] = "waiting_message"
                        response_text = f"{recipient} kişisine ne yazmak istersiniz?"
                    else:
                        state_data["state"] = "waiting_recipient"
                        response_text = "Kime mesaj göndermek istersiniz?"

                else:
                    sys_res = execute_command(query_text)
                    if sys_res:
                        response_text = sys_res
                    else:
                        stream = get_ai_response_stream(query_text)
                        if stream:
                            for chunk in stream:
                                content = chunk.choices[0].delta.content
                                if content: response_text += content

                if response_text:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as voice_resp:
                        await speak_edge_tts(response_text, voice_resp.name)
                        with open(voice_resp.name, "rb") as f:
                            await update.message.reply_voice(voice=f, caption=response_text)
                    if os.path.exists(voice_resp.name): os.remove(voice_resp.name)
                
                self.is_processing = False
        except Exception as e:
            log(f"Telegram Handle Error: {e}")
            self.is_processing = False

    def apply_window_styles(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0: hwnd = self.winfo_id()
            
            # Get current style
            style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
            
            # WS_EX_TOOLWINDOW (0x80) -> Hide from taskbar
            # WS_EX_TRANSPARENT (0x20) -> Click-through (ignore mouse events)
            # WS_EX_LAYERED (0x80000) -> Required for some transparency effects
            style |= 0x00000080 | 0x00000020 | 0x00080000
            
            ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, style)
            
            # Set to bottom (HWND_BOTTOM = 1)
            # SWP_NOSIZE = 0x0001, SWP_NOMOVE = 0x0002, SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except Exception as e:
            log(f"Window Style Error: {e}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def manual_interrupt(self, event=None):
        if self.in_conversation or self.is_speaking or self.is_processing:
            self.system_print("MANUAL RESET INTERRUPT", is_ai=True)
            self.interrupted = True
            import pygame
            pygame.mixer.music.stop()

    def initial_greeting(self):
        time.sleep(1.5)
        self.jarvis_speak("Hoşgeldiniz efendim. Hizmetinizdeyim.")

    def system_print(self, text, is_user=False, is_ai=False):
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[SYS]"
        if is_user: prefix = "[gok2]"; text = text.upper()
        elif is_ai: prefix = "[J.A.R.V.I.S.]"
        print(f"<{timestamp}> {prefix} {text}")

    def jarvis_speak(self, text):
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
        self.handle_user_input(query)

        # WhatsApp Flow
        if self.whatsapp_state == "waiting_recipient":
            # Name extraction with suffix removal (e.g., Ali'ye -> Ali)
            clean_name = re.sub(r'(y[ea]|[ea])$', '', query.lower().strip())
            self.temp_recipient = clean_name
            self.jarvis_speak("Mesaj içeriği nedir?")
            self.whatsapp_state = "waiting_message"
            self.is_processing = False
            return

        if self.whatsapp_state == "waiting_message":
            from ai_brain import send_whatsapp_message
            message_content = query
            self.jarvis_speak(f"{self.temp_recipient} kişisine mesajınız gönderiliyor.")
            if send_whatsapp_message(self.temp_recipient, message_content):
                self.jarvis_speak("Mesaj başarıyla iletildi efendim.")
            else:
                self.jarvis_speak("Mesaj gönderilirken bir hata oluştu.")
            
            self.whatsapp_state = None
            self.temp_recipient = None
            self.is_processing = False
            return

        if any(kw in query.lower() for kw in ["mesaj gönder", "mesaj at", "whatsapp"]):
            # Check if recipient is in the initial command, e.g., "Ali'ye mesaj gönder"
            match = re.search(r'(.*?)([\'"]?[ye]?[ea])?\s+(mesaj gönder|mesaj at|whatsapp)', query.lower())
            if match and match.group(1).strip():
                recipient = match.group(1).strip()
                # Clean suffix
                recipient = re.sub(r'(y[ea]|[ea])$', '', recipient)
                self.temp_recipient = recipient
                self.whatsapp_state = "waiting_message"
                self.jarvis_speak(f"{recipient} kişisine ne yazmak istersiniz?")
            else:
                self.jarvis_speak("Kime mesaj göndermek istersiniz?")
                self.whatsapp_state = "waiting_recipient"
            
            self.is_processing = False
            return

        response = execute_command(query)
        if response:
            self.jarvis_speak(response)
        elif any(kw in query for kw in ["ara", "bul", "nedir", "kimdir"]):
            term = search_web(query)
            if term: self.jarvis_speak(f"İnternette {term} araştırılıyor.")
        else:
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
                            if len(clean_sent) > 2: self.jarvis_speak(clean_sent)
                            current_sentence = ""
                if current_sentence.strip() and not self.interrupted:
                    self.jarvis_speak(current_sentence.strip())
        self.is_processing = False

    def handle_user_input(self, input_text):
        ai_brain.process_user_command(input_text)

    def conversation_loop(self):
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        recognizer.energy_threshold = 5000
        try:
            with sr.Microphone(device_index=self.mic_index) as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                while self.in_conversation:
                    try:
                        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                        query = transcribe_audio(audio)
                        if not query or len(query) < 3: continue
                        if any(phrase in query for phrase in ["m.k.", "altyazı", "altyazi"]): continue
                        
                        self.system_print(query, is_user=True)
                        if any(cmd in query for cmd in ["bay bay"]):
                            self.jarvis_speak("İyi günler efendim.")
                            self.after(1000, self.destroy)
                            return
                        if any(cmd in query for cmd in ["uyu", "bekle"]):
                            self.jarvis_speak("Sistem bekleme modunda.")
                            self.in_conversation = False
                            break
                        self.process_query(query)
                    except: continue
        except: pass

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
                            if text and ("jarvis" or "jarvis orda mısın" or "babacık eve geldi") in text:
                                self.jarvis_speak("Buyrun efendim.")
                                self.in_conversation = True
                                threading.Thread(target=self.conversation_loop, daemon=True).start()
                        except: pass
                except: time.sleep(2)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
