import os
import tempfile
import pygame
import asyncio
import edge_tts
import speech_recognition as sr
from config import client_eleven, client_groq, log
from arm_controller import arm

# Windows Ses Kontrolü İçin
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def find_mic_index():
    try:
        mic_list = sr.Microphone.list_microphone_names()
        for index, name in enumerate(mic_list):
            if "steelseries" in name.lower(): return index
        return None
    except: return None

def transcribe_audio(audio_data):
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
    except Exception as e:
        log(f"Transcription error: {e}")
        return None

async def speak_edge_tts(text, path):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="-5%", pitch="-10Hz")
    await communicate.save(path)

def speak(text, interrupt_check_callback):
    if not text.strip(): return

    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name

        try:
            if client_eleven:
                audio_iterator = client_eleven.text_to_speech.convert(
                    text=text,
                    voice_id="pNInz6obpgDQGcFmaJgB",
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                with open(tmp_path, "wb") as f:
                    for chunk in audio_iterator:
                        if chunk: f.write(chunk)
            else: raise Exception()
        except:
            asyncio.run(speak_edge_tts(text, tmp_path))

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            pygame.mixer.music.load(tmp_path)
            
            # Kol Hareketini Başlat
            arm.start_talking_animation()
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy() and not interrupt_check_callback():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # Kol Hareketini Durdur
            arm.stop_talking_animation()

            try: os.remove(tmp_path)
            except: pass
    except Exception as e:
        log(f"AUDIO_ERR: {e}")
        arm.stop_talking_animation()

def provide_voice_feedback(message):
    # Utilizing the existing speak function for voice feedback
    speak(message, lambda: False)

class MusicPlayer:
    def __init__(self):
        self._volume = 0.5
        # Jarvis'in kendi konuşma sesi her zaman %100 (veya sabit bir değer) kalsın
        # Sistem sesi kısıldığında Jarvis'in duyulabilirliği azalmasın
        pygame.mixer.music.set_volume(1.0) 
        self._sync_with_system()

    @property
    def volume(self):
        self._sync_with_system()
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value

    def _sync_with_system(self):
        """Sistem ses seviyesini çeker."""
        try:
            device = AudioUtilities.GetSpeakers()
            self._volume = device.EndpointVolume.GetMasterVolumeLevelScalar()
        except:
            pass

    def set_system_volume(self, level):
        """Windows ana ses seviyesini ayarlar (0.0 - 1.0)."""
        try:
            device = AudioUtilities.GetSpeakers()
            device.EndpointVolume.SetMasterVolumeLevelScalar(level, None)
            return True
        except Exception as e:
            log(f"SYSTEM_VOLUME_ERR: {e}")
            return False

    def adjust_volume(self, volume_level):
        """Sadece Windows ana ses seviyesini ayarlar."""
        try:
            target_vol = max(0.0, min(1.0, float(volume_level)))
            
            # Windows Genel Ses Seviyesini Güncelle
            self.set_system_volume(target_vol)
            
            self._volume = target_vol
            log(f"SISTEM_SES_SEVIYESI: %{int(target_vol * 100)}")
            return target_vol
        except Exception as e:
            log(f"VOLUME_ADJUST_ERR: {e}")
            return None
