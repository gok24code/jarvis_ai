from config import client_groq
from audio_handler import MusicPlayer  # Erişilebilirlik için eklendi

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

