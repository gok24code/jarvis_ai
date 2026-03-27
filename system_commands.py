import webbrowser
import subprocess
import ctypes
import os
from config import TARGET_DIR, DISCORD_PATH, SPOTIFY_PATH, BLENDER_PATH

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
    # Web Siteleri
    sites = {
        "youtube": "https://www.youtube.com", 
        "gitab": "https://github.com/gok24code?tab=repositories", 
        "versel": "https://vercel.com", 
        "şirket": "https://prometh-labs.vercel.app/"
    }
    
    for site, url in sites.items():
        if site in query and ("aç" in query or "git" in query):
            open_url(url)
            return f"{site.capitalize()} açılıyor efendim."

    # Uygulamalar
    if "discord" in query and "aç" in query:
        cmd = f'start "" "{DISCORD_PATH}" --processStart Discord.exe'
        subprocess.Popen(cmd, shell=True)
        return "Discord açılıyor efendim."

    if "gemini" in query and "terminal" in query:
        os.system(f'start cmd /k "cd /d {TARGET_DIR} && gemini"')
        return "Gemini başlatılıyor."
        
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
    if any(k in query for k in ["spotify", "müzik", "şarkı"]) and ("aç" in query or "çal" in query):
        os.startfile("spotify:")
        # Uygulamanın açılması için kısa bir bekleme ve play tuşu simülasyonu
        time.sleep(2)
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0) # VK_MEDIA_PLAY_PAUSE
        return "Playlist çalınıyor efendim."

    if any(k in query for k in ["blender", "tasarım","çizim"]) and ("aç" in query or "başlat" in query):
        subprocess.Popen([BLENDER_PATH])
        return "Blender açılıyor efendim. Bugün ne üstünde çalışacaksınız?"

    if any(k in query for k in ["müziği durdur", "şarkıyı durdur", "müziği duraklat", "şarkıyı duraklat"]):
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        return "Müzik duraklatıldı."
    return None