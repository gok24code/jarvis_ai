import os
import asyncio
import tempfile
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
from ai_brain import get_ai_response_stream
from audio_handler import speak_edge_tts, transcribe_audio
from system_commands import execute_command
from config import TELEGRAM_TOKEN, AUTHORIZED_USER_ID, GROQ_API_KEY, log

# Logger ayarları
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yetki kontrolü
    if AUTHORIZED_USER_ID and update.effective_user.id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Üzgünüm efendim, sadece yöneticime cevap verebilirim.")
        return

    query_text = ""
    ogg_path = None
    wav_path = None

    try:
        # Eğer mesaj SESLİ ise
        if update.message.voice:
            voice = await update.message.voice.get_file()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as ogg_file:
                await voice.download_to_drive(ogg_file.name)
                ogg_path = ogg_file.name

            # OGG'den WAV'a çevir
            wav_path = ogg_path.replace(".ogg", ".wav")
            audio = AudioSegment.from_file(ogg_path)
            audio.export(wav_path, format="wav")

            # Transcribe (Whisper via Groq)
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                query_text = transcribe_audio(audio_data)

        # Eğer mesaj METİN ise
        elif update.message.text:
            query_text = update.message.text

        if not query_text:
            await update.message.reply_text("Sizi tam olarak anlayamadım efendim.")
            return

        log(f"Telegram User: {query_text}")

        # ÖNCE KOMUTLARI KONTROL ET (Spotify, Uygulama Açma, Proje Modu vb.)
        cmd_response = execute_command(query_text.lower())

        if cmd_response:
            # Eğer bu bir komutsa ve işlendiyse, sonucu gönder ve bitir
            await update.message.reply_text(f"Jarvis: {cmd_response}")
            return

        # EĞER KOMUT DEĞİLSE, NORMAL SOHBET OLARAK DEVAM ET
        status_msg = await update.message.reply_text("Anlıyorum efendim, düşünülüyor...")


        # Jarvis'in Beynine Sor
        response_text = ""
        stream = get_ai_response_stream(query_text)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content: response_text += content
        
        if not response_text:
            await status_msg.edit_text("Bir hata oluştu efendim.")
            return

        # Cevabı Seslendir
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as voice_resp:
            await speak_edge_tts(response_text, voice_resp.name)
            voice_path = voice_resp.name

        # Sesli Mesaj Gönder
        with open(voice_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file, caption=response_text)
        
        await status_msg.delete()

        # Temizlik
        if ogg_path and os.path.exists(ogg_path): os.remove(ogg_path)
        if wav_path and os.path.exists(wav_path): os.remove(wav_path)
        if os.path.exists(voice_path): os.remove(voice_path)

    except Exception as e:
        log(f"Telegram Bridge Error: {e}")
        await update.message.reply_text(f"Hata oluştu: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Jarvis Uzaktan Erişim Sistemi Aktif.\nID'niz: {user_id}\nLütfen sesli bir komut verin efendim.")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("Lütfen .env dosyası içinde TELEGRAM_TOKEN tanımlayın.")
    else:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(MessageHandler(filters.VOICE, handle_voice))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_voice)) # Yazılı da cevap verebilir
        application.add_handler(MessageHandler(filters.COMMAND, start))
        
        print("Jarvis Telegram Botu Başlatılıyor...")
        application.run_polling()
