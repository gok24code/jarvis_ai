import webbrowser
import subprocess
import ctypes
import os
from config import TARGET_DIR, DISCORD_PATH

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

    if "bilgisayarı kilitle" in query:
        #win+L
        ctypes.windll.user32.LockWorkStation()
        return "Tekrar hoşgeldiniz."
    if "temizlik" in query:
        subprocess.Popen("cleanmgr.exe")
        return "Sistemin tozunu bir alalım bakalım. Temizlik aracı çalıştırılıyor."
    return None
