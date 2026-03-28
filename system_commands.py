import webbrowser
import subprocess
import ctypes
import os
from config import TARGET_DIR, DISCORD_PATH, SPOTIFY_PATH, BLENDER_PATH, HOLOGRAM_PATH

import time

def open_url(url):
    webbrowser.open(url)

def search_web(query):
    search_term = query.replace("ara", "").replace("bul", "").replace("internette", "").strip()
    if search_term:
        url = f"https://duckduckgo.com/?q={search_term}"
        open_url(url)
        return search_term
    return None

def execute_command(query):
    # ... (diğer komutlar aynı kalıyor)
    sites = {
        "video": "https://www.youtube.com", 
        "gitab": "https://github.com/gok24code?tab=repositories", 
        "versel": "https://vercel.com", 
        "şirket": "https://prometh-labs.vercel.app/"
    }
    
    for site, url in sites.items():
        if site in query and ("aç" in query or "git" in query):
            open_url(url)
            return f"{site.capitalize()} platformu açılıyor efendim."

    # Uygulamalar
    if "discord" in query and "aç" in query:
        cmd = f'start "" "{DISCORD_PATH}" --processStart Discord.exe'
        subprocess.Popen(cmd, shell=True)
        return "Discord açılıyor efendim."

    if "gemini" in query and "terminal" in query:
        from ai_brain import generate_gemini_prompt
        project_desc = query.replace("gemini", "").replace("terminal", "").replace("aç", "").replace("yap", "").replace("projesi", "").strip()
        
        if not project_desc or len(project_desc) < 3:
            os.system(f'start cmd /k "cd /d {TARGET_DIR} && gemini"')
            return "Gemini terminali başlatılıyor efendim."
        
        # AI ile klasör ismi ve teknik prompt oluştur
        ai_output = generate_gemini_prompt(project_desc)
        
        # Basit ayrıştırma (parsing)
        try:
            folder_line = [l for l in ai_output.split("\n") if "FOLDER_NAME:" in l][0]
            prompt_line = [l for l in ai_output.split("\n") if "PROMPT:" in l][0]
            
            folder_name = folder_line.split("FOLDER_NAME:")[1].strip()
            detailed_prompt = prompt_line.split("PROMPT:")[1].strip()
        except:
            folder_name = "new-project"
            detailed_prompt = project_desc

        # Proje klasörünü oluştur
        new_project_path = os.path.join(TARGET_DIR, folder_name)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path)
            
        # Tırnak işaretlerini terminal uyumluluğu için düzenle
        escaped_prompt = detailed_prompt.replace('"', '\"')
        
        # Gemini'yi YENİ klasörün içinde başlat
        os.system(f'start cmd /k "cd /d {new_project_path} && gemini \"{escaped_prompt}\""')
        return f"Efendim, {folder_name} klasörü oluşturuldu ve Gemini'ye talimatlar iletildi."
        
    if "editör" in query:
        subprocess.Popen(["code", TARGET_DIR], shell=True)
        return "Editör açılıyor."
        
    if "terminal" in query:
        subprocess.Popen(["wt.exe", "-d", TARGET_DIR], shell=True)
        return "Terminal açılıyor."

    if "sistemi kilitle" in query:
        #win+L
        ctypes.windll.user32.LockWorkStation()
        return "uygulandı."
    if "temizlik" in query:
        subprocess.Popen("cleanmgr.exe")
        return "Sistemin tozunu bir alalım bakalım. Temizlik aracı çalıştırılıyor."
    # Basit Müzik ve Spotify Kontrolü
    if any(k in query for k in ["spotify", "müzik aç", "şarkı aç"]):
        os.startfile("spotify:")
        time.sleep(1.5)
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0) # Play/Pause tuşu
        return "Spotify açılıyor ve müzik başlatılıyor efendim."

    if any(k in query for k in ["müziği durdur", "müziği duraklat", "çalmayı kes"]):
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0) # Play/Pause tuşu
        return "Müzik durduruldu."

    if any(k in query for k in ["müziği geç", "sıradaki parça", "müziği atla"]):
        ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0) # Sıradaki parça tuşu
        return "Sıradaki parça."

    if any(k in query for k in ["blender", "tasarım","çizim"]) and ("aç" in query or "başlat" in query):
        subprocess.Popen([BLENDER_PATH])
        # Hologram projesini de başlat
        hologram_dir = os.path.dirname(HOLOGRAM_PATH)
        subprocess.Popen(f'python "{HOLOGRAM_PATH}"', cwd=hologram_dir, shell=True)
        return "Blender ve Hologram arayüzü açılıyor efendim. Bugün ne üstünde çalışacaksınız?"

    return None