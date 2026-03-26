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
