import customtkinter as ctk
import speech_recognition as sr
import threading
import time
import re
import tkinter as tk
import os
import asyncio
import tempfile
from config import *
from audio_handler import find_mic_index, transcribe_audio, speak, speak_edge_tts
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

        # UI Ayarları
        self.geometry(f"{HUD_WIDTH}x{HUD_HEIGHT}+10+10")
        self.overrideredirect(True) 
        self.attributes("-topmost", True)
        self.config(bg='black')
        self.attributes("-transparentcolor", "black")

        self.after(100, self.hide_from_taskbar)

        self.canvas = tk.Canvas(self, width=HUD_WIDTH, height=HUD_HEIGHT, 
                               bg='black', highlightthickness=0, bd=0)
        self.canvas.pack()

        self.top_left_text = self.canvas.create_text(
            5, 20, text="J.A.R.V.I.S.", anchor="nw",
            fill=COLOR_HUD, font=("Consolas", 18, "bold")
        )
        self.status_dot = self.canvas.create_oval(
            175, 30, 190, 45, 
            fill=COLOR_HUD, outline=COLOR_HUD
        )

        # Sağ Tık Menüsü (Ses Kontrolü için)
        self.menu = tk.Menu(self, tearoff=0, bg="black", fg=COLOR_HUD, activebackground=COLOR_HUD, activeforeground="black")
        self.menu.add_command(label="WhatsApp Mesajı", command=self.open_whatsapp_dialog)
        self.menu.add_separator()
        self.menu.add_command(label="Ses %100", command=lambda: volume_manager.set_volume(100))
        self.menu.add_command(label="Ses %70", command=lambda: volume_manager.set_volume(70))
        self.menu.add_command(label="Ses %50", command=lambda: volume_manager.set_volume(50))
        self.menu.add_command(label="Ses %30", command=lambda: volume_manager.set_volume(30))
        self.menu.add_command(label="Sessiz", command=lambda: volume_manager.set_volume(0))
        self.menu.add_separator()
        self.menu.add_command(label="Çıkış", command=self.destroy)

        self.bind("<Button-3>", self.show_menu)

        # Durum Değişkenleri

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

        self.pulse_animation()
        
        self.bind_all("<r>", self.manual_interrupt)
        self.bind_all("<R>", self.manual_interrupt)

    def open_whatsapp_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("WhatsApp Mesajı")
        dialog.geometry("300x200")
        dialog.config(bg="black")
        dialog.attributes("-topmost", True)

        tk.Label(dialog, text="Alıcı (İsim veya Numara):", fg=COLOR_HUD, bg="black").pack(pady=5)
        recipient_entry = tk.Entry(dialog, bg="#111", fg=COLOR_HUD, insertbackground=COLOR_HUD)
        recipient_entry.pack(pady=5, padx=20, fill="x")

        tk.Label(dialog, text="Mesaj:", fg=COLOR_HUD, bg="black").pack(pady=5)
        message_entry = tk.Entry(dialog, bg="#111", fg=COLOR_HUD, insertbackground=COLOR_HUD)
        message_entry.pack(pady=5, padx=20, fill="x")

        def send():
            recipient = recipient_entry.get()
            message = message_entry.get()
            if recipient and message:
                from ai_brain import send_whatsapp_message
                if send_whatsapp_message(recipient, message):
                    self.jarvis_speak(f"{recipient} kişisine mesaj gönderildi.")
                else:
                    self.jarvis_speak("Mesaj gönderilemedi efendim.")
                dialog.destroy()

        tk.Button(dialog, text="Gönder", command=send, bg=COLOR_HUD, fg="black").pack(pady=20)

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

    def hide_from_taskbar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd == 0: hwnd = self.winfo_id()
            style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
            style |= 0x00000080
            ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, style)
            self.attributes("-topmost", True)
        except: pass

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
        self.jarvis_speak("Jarvis protokolü aktif, efendim. Hizmetinizdeyim.")

    def pulse_animation(self):
        status_color = COLOR_HUD
        if self.is_speaking or self.in_conversation: status_color = COLOR_LISTENING
        elif self.is_processing: status_color = COLOR_PROCESSING
        else:
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
                        if any(cmd in query for cmd in ["beklemede kal", "bekle", "güle güle"]):
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
                            if text and "jarvis" in text:
                                self.jarvis_speak("Buyrun efendim.")
                                self.in_conversation = True
                                threading.Thread(target=self.conversation_loop, daemon=True).start()
                        except: pass
                except: time.sleep(2)

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
