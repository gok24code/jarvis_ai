from config import client_groq
from audio_handler import MusicPlayer, provide_voice_feedback  # Erişilebilirlik için eklendi
import system_commands
import audio_handler
from whatsapp_handler import WhatsAppHandler
from person_pool import PersonPool

# Initialize handlers
whatsapp_handler = WhatsAppHandler()
person_pool = PersonPool()

def process_user_command(command):
    if 'launch steam' in command:
        system_commands.launch_steam()
        audio_handler.provide_voice_feedback("Steam launched. Entering game mode.")
    elif 'launch epic games' in command:
        system_commands.launch_epic_games()
        audio_handler.provide_voice_feedback("Epic Games Launcher launched. Entering game mode.")

def send_whatsapp_message(recipient_name_or_alias, message_text):
    """
    Sends a WhatsApp message using the WhatsAppHandler and PersonPool.
    """
    # Her gönderimden önce rehberi tazele (Dosyadan yeniden oku)
    person_pool.load_pool()
    
    phone_number = person_pool.get_phone_number(recipient_name_or_alias)
    
    if not phone_number:
        # If not found in pool, check if it's a direct phone number
        import re
        if re.match(r'^\+?[1-9]\d{1,14}$', recipient_name_or_alias.replace(" ", "")):
            phone_number = recipient_name_or_alias.replace(" ", "")
        else:
            msg = f"[ERROR]: Recipient '{recipient_name_or_alias}' not found in persons.json and is not a valid phone number."
            print(msg)
            return False

    return whatsapp_handler.send_message(phone_number, message_text)

def get_ai_response_stream(query, system_prompt=None):
    if not system_prompt:
        system_prompt = "Adın Jarvis. Karizmatik, ağırbaşlı, mütvazi ve son derece zeki bir yapay zekasın. Cevapların kısa, öz ve bir beyefendi (gentleman) tarzında olsun. Türkçe konuşuyorsun."

    try:
        stream = client_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            stream=True,
        )
        return stream
    except Exception as e:
        print(f"AI Stream Error: {e}")
        return None

def generate_gemini_prompt(user_request):
    """Kullanıcının isteğini Gemini CLI için klasör ismi ve teknik direktife dönüştürür."""
    system_prompt = (
        "Sen bir kıdemli yazılım mimarısın. Kullanıcının proje isteğini al ve "
        "Gemini CLI için iki şey üret:\n"
        "1. FOLDER_NAME: Proje için kısa, İngilizce, küçük harfli ve boşluksuz bir klasör ismi (örn: weather-app).\n"
        "2. PROMPT: Gemini'ye verilecek çok detaylı, teknik ve adım adım İngilizce direktif.\n"
        "Çıktın SADECE şu formatta olmalı:\n"
        "FOLDER_NAME: [isim]\n"
        "PROMPT: [direktif]"
    )
    
    try:
        response = client_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Proje İsteği: {user_request}"}
            ],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Prompt Generation Error: {e}")
        return f"FOLDER_NAME: temp-project\nPROMPT: {user_request}" # Hata payı için fallback

def generate_self_improvement_prompt(user_request):
    """Kullanıcının Jarvis'i geliştirme isteğini detaylı bir teknik direktife dönüştürür."""
    system_prompt = (
        "Sen Jarvis'in kıdemli bir sistem mimarısın. Kullanıcı senden Jarvis'in (yani senin) kod tabanına "
        "yeni bir özellik eklemeni veya mevcut bir özelliği iyileştirmeni istiyor.\n\n"
        "Şu anki projenin yapısı Python tabanlıdır ve modüller şunlardır: jarvis_ui.pyw, ai_brain.py, audio_handler.py, system_commands.py, config.py.\n"
        "Gemini CLI'ya iletilecek SADECE çok detaylı, teknik ve adım adım bir İngilizce direktif üret (PROMPT).\n"
        "Lütfen Gemini CLI'a bu değişikliği yaparken diğer fonksiyonları bozmamasını, mevcut yapıyı ve imports'u korumasını tembihle.\n"
        "Çıktın SADECE şu formatta olmalı:\n"
        "PROMPT: [direktif]"
    )
    
    try:
        response = client_groq.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Geliştirme İsteği: {user_request}"}
            ],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Self-Improvement Prompt Generation Error: {e}")
        return f"PROMPT: You are tasked to improve the current Jarvis Python codebase. Request: {user_request}"

