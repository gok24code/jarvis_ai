from config import client_groq

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
