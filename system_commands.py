import webbrowser
import subprocess
import ctypes
import os
import platform
import config
from config import TARGET_DIR, DISCORD_PATH, BLENDER_PATH, HOLOGRAM_PATH, ZEN_PATH

import time

def open_url(url):
    webbrowser.open(url)

def launch_steam():
    try:
        subprocess.Popen([config.LAUNCHER_PATHS['steam']])
    except Exception as e:
        print(f"Error launching Steam: {e}")

def launch_epic_games():
    try:
        subprocess.Popen([config.LAUNCHER_PATHS['epic_games']])
    except Exception as e:
        print(f"Error launching Epic Games Launcher: {e}")

def search_web(query):
    search_term = query.replace("ara", "").replace("bul", "").replace("internette", "").strip()
    if search_term:
        url = f"https://duckduckgo.com/?q={search_term}"
        open_url(url)
        return search_term
    return None

import threading
from audio_handler import speak, MusicPlayer

class VolumeController:
    def __init__(self):
        self.player = MusicPlayer()

    def set_volume(self, level):
        """0-100 arası bir değer bekler ve bunu adjust_volume'a iletir."""
        normalized_level = level / 100.0
        return self.player.adjust_volume(normalized_level)

volume_manager = VolumeController()

def run_gemini_integrated(project_path, prompt, folder_name):
    def target():
        print(f"\n[SYSTEM]: Gemini Agent {folder_name} üzerinde çalışmaya başladı (YOLO Mode Active)...")
        
        # Geçici prompt dosyası yolu
        temp_prompt_file = os.path.join(project_path, f".{folder_name}_prompt.txt")
        
        try:
            # Prompt'u bir dosyaya yaz (UTF-8)
            with open(temp_prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            
            # PowerShell'e dosyayı okuyup Gemini'ye iletmesini söyleyen komut
            # -Raw bayrağı tüm dosyayı tek bir string olarak okur (satır sonlarını korur)
            full_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Get-Content -Path \'{temp_prompt_file}\' -Raw; gemini --yolo -p $p"'
            
            process = subprocess.Popen(
                full_command,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                encoding='utf-8',
                errors='replace'
            )

            # Çıktıyı terminale yazdır (izleme için)
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    print(f"[{folder_name}]: {line.strip()}")
            
            process.wait()
            
            # Geçici dosyayı sil
            if os.path.exists(temp_prompt_file):
                os.remove(temp_prompt_file)
            
            # İşlem bittiğinde sesli bildirim yap
            finish_msg = f"Efendim, {folder_name} projesinin kodlama işlemleri tamamlandı. Dosyalar hazır."
            print(f"\n[SYSTEM]: {finish_msg}")
            speak(finish_msg, lambda: False)

            # Telegram bildirimi gönder (Circular import önlemek için lokal import)
            try:
                from telegram_bridge import send_telegram_notification
                send_telegram_notification(finish_msg)
            except Exception as te:
                print(f"[ERROR]: Telegram bildirimi gönderilirken hata: {te}")
            
        except Exception as e:
            # Hata durumunda da temizlik yapmaya çalış
            if os.path.exists(temp_prompt_file):
                os.remove(temp_prompt_file)
            
            error_msg = f"Gemini çalışırken bir hata oluştu: {str(e)}"
            print(f"[ERROR]: {error_msg}")
            speak("Üzgünüm efendim, kodlama sırasında bir aksaklık yaşandı.", lambda: False)

    threading.Thread(target=target, daemon=True).start()

# Proje oluşturma durumu için global değişkenler
project_creation_state = {
    "active": False,
    "step": 0, # 0: İsim bekleniyor, 1: Detay bekleniyor
    "folder_name": "",
    "description": ""
}

# Jarvis kendini geliştirme durumu için global değişkenler
self_improvement_state = {
    "active": False,
    "description": ""
}

def execute_command(query):
    if not query: return None
    
    # Temizlik ve Jarvis ismini ayıklama (isteğe bağlı, genel deneyimi iyileştirir)
    query_clean = query.lower().replace("hey jarvis", "").replace("jarvis", "").strip()
    if not query_clean: return None

    # Komutları bağlaçlara göre ayır
    conjunctions = [" ve ", " ayrıca ", " bir de ", " ardından ", " sonra "]
    parts = [query_clean]
    
    for conj in conjunctions:
        new_parts = []
        for p in parts:
            if conj in p:
                new_parts.extend(p.split(conj))
            else:
                new_parts.append(p)
        parts = new_parts
    
    parts = [p.strip() for p in parts if p.strip()]
    
    if len(parts) > 1:
        responses = []
        for part in parts:
            res = _handle_single_command(part)
            if res:
                responses.append(res)
        
        if not responses: return None
        # Yanıtları birleştir
        return " ".join(responses)
    else:
        return _handle_single_command(query_clean)

def _handle_single_command(query):
    global project_creation_state
    global self_improvement_state

    # 1. WEB SİTELERİ
    sites = {
        "video": "https://www.youtube.com", 
        "github": "https://github.com/gok24code?tab=repositories", 
        "versel": "https://vercel.com", 
        "şirket": "https://prometh-labs.vercel.app/"
    }
    
    for site, url in sites.items():
        if site in query and ("aç" in query or "git" in query):
            open_url(url)
            return f"{site.capitalize()} platformu açılıyor efendim."

    # 2. UYGULAMALAR
    if "discord" in query and "aç" in query:
        cmd = f'start "" "{DISCORD_PATH}" --processStart Discord.exe'
        subprocess.Popen(cmd, shell=True)
        return "Discord açılıyor efendim."

    if "tarayıcı" in query:
        cmd = f'start "" "{ZEN_PATH}" --processStart zen.exe'
        subprocess.Popen(cmd, shell=True)
        return "En sevdiğiniz tarayıcınız açılıyor efendim."

    if "steam" in query and "aç" in query:
        launch_steam()
        return "Steam açılıyor efendim. Oyun modu aktif ediliyor."

    if "epic games" in query and "aç" in query:
        launch_epic_games()
        return "Epic Games Launcher açılıyor efendim."

    if "oyun modu" in query:
        launch_steam()
        launch_epic_games()
        return "Oyun modu protokolü başlatıldı. Steam ve Epic Games Launcher açılıyor. İyi oyunlar efendim."
        
    if "kod" in query:
        subprocess.Popen(["code", TARGET_DIR], shell=True)
        return "Vijul stüdyo kod açılıyor."
    
    if "terminal" in query:
        subprocess.Popen(["wt.exe", "-d", TARGET_DIR], shell=True)
        return "Terminal açılıyor."

    # 3. SİSTEM KOMUTLARI
    if "kilitle" in query:
        ctypes.windll.user32.LockWorkStation()
        return "uygulandı."

    if "temizlik" in query:
        subprocess.Popen("cleanmgr.exe")
        return "Sistemin tozunu bir alalım bakalım. Temizlik aracı çalıştırılıyor."

    if any(k in query for k in ["alanı temizle"]):
        ps_cmd = (
            'Get-Process | Where-Object { $_.MainWindowTitle -ne "" -and $_.ProcessName -ne "explorer" '
            '-and $_.ProcessName -ne "python" -and $_.ProcessName -ne "pythonw" } | Stop-Process -Force'
        )
        subprocess.Popen(["powershell", "-Command", ps_cmd], shell=True)
        return "Tüm kullanıcı programları sonlandırılıyor efendim. Çalışma alanınız temizlendi."

    if any(k in query for k in ["bilgisayarı kapat", "sistemi kapat"]):
        subprocess.Popen(["shutdown", "/s", "/t", "5"], shell=True)
        return "Sistem beş saniye içinde kapatılacak efendim. İyi günler dilerim."

    if any(k in query for k in ["yeniden başlat", "sistemi yeniden başlat"]):
        subprocess.Popen(["shutdown", "/r", "/t", "5"], shell=True)
        return "Sistem beş saniye içinde yeniden başlatılacak efendim."

    # 4. SES KONTROLÜ
    if "ses" in query:
        import re
        numbers = re.findall(r'\d+', query)
        if numbers:
            level = int(numbers[0])
            volume_manager.set_volume(level)
            return f"Ses seviyesi yüzde {level} olarak ayarlandı efendim."
        
        if "aç" in query or "artır" in query or "yükselt" in query:
            new_vol = min(1.0, volume_manager.player.volume + 0.1)
            volume_manager.player.adjust_volume(new_vol)
            return f"Ses seviyesi artırıldı efendim."
            
        if "kıs" in query or "azalt" in query:
            new_vol = max(0.0, volume_manager.player.volume - 0.1)
            volume_manager.player.adjust_volume(new_vol)
            return f"Ses seviyesi kısıldı efendim."

    # 5. MÜZİK VE SPOTIFY
    if any(k in query for k in ["spotify", "şarkı","müzik"]) and ("aç" in query or "başlat" in query):
        os.startfile("spotify:")
        time.sleep(1.5)
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0) # Play/Pause tuşu
        return "Tabiki efendim."

    if any(k in query for k in ["çalmayı", "duraklat"]) and (query or "durdur" in query or "kes" in query):
        ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
        return "İstediğiniz gibi."

    if any(k in query for k in ["sıradaki", "sonraki", "geç"]):
        ctypes.windll.user32.keybd_event(0xB0, 0, 0, 0)
        return "Tabii efendim."

    # 6. TASARIM VE BLENDER
    if any(k in query for k in ["blender", "tasarım","çizim"]) and ("aç" in query or "başlat" in query):
        subprocess.Popen([BLENDER_PATH])
        hologram_dir = os.path.dirname(HOLOGRAM_PATH)
        subprocess.Popen(f'python "{HOLOGRAM_PATH}"', cwd=hologram_dir, shell=True)
        return "Blender ve Hologram arayüzü açılıyor efendim. Bugün ne üstünde çalışacaksınız?"

    # 8. GEMINI HIZLI PROJE (Bağımsız)
    if "gemini" in query:
        from ai_brain import generate_gemini_prompt
        project_desc = query.replace("gemini", "").replace("terminal", "").replace("aç", "").replace("yap", "").replace("projesi", "").replace("oluştur", "").strip()
        
        if not project_desc or len(project_desc) < 3:
            return "Efendim, hangi projeyi yapmamı istediğinizi tam anlayamadım."
        
        ai_output = generate_gemini_prompt(project_desc)
        try:
            lines = ai_output.split("\n")
            folder_name = "new-project"
            detailed_prompt = project_desc
            for line in lines:
                if "FOLDER_NAME:" in line:
                    folder_name = line.split("FOLDER_NAME:")[1].strip()
                elif "PROMPT:" in line:
                    detailed_prompt = line.split("PROMPT:")[1].strip()
        except:
            folder_name = "new-project"
            detailed_prompt = project_desc

        new_project_path = os.path.join(TARGET_DIR, folder_name)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path)
            
        run_gemini_integrated(new_project_path, detailed_prompt, folder_name)
        return f"Tabii efendim, {folder_name} klasörünü hazırladım ve Arka planda çalışmaya başladım."

    # 8. SELF-IMPROVEMENT MODU (Aktifse)
    if self_improvement_state["active"]:
        if "iptal" in query or "vazgeç" in query:
            self_improvement_state = {"active": False, "description": ""}
            return "Sistem güncelleme modu iptal edildi efendim."
            
        user_input = query.strip().lower()
        if any(k in user_input for k in ["tamamdır", "bu kadar", "hazır", "başla", "tamam"]):
            description = self_improvement_state["description"]
            if not description:
                return "Efendim, henüz herhangi bir detay vermediniz. Lütfen neyi değiştirmemi istediğinizi anlatın veya iptal deyin."
                
            from ai_brain import generate_self_improvement_prompt
            ai_output = generate_self_improvement_prompt(description)
            
            if "PROMPT:" in ai_output:
                detailed_prompt = ai_output.split("PROMPT:")[1].strip()
            else:
                detailed_prompt = description
                
            current_dir = os.path.dirname(os.path.abspath(__file__))
            run_gemini_integrated(current_dir, detailed_prompt, "jarvis-self-improvement")
            
            self_improvement_state = {"active": False, "description": ""}
            return "Talimatlarınızı aldım efendim. Sistem çekirdeğimi güncellemeye başlıyorum."
        else:
            self_improvement_state["description"] += query + " "
            return "Not aldım efendim. Başka bir detay var mı?"

    # 9. SELF-IMPROVEMENT BAŞLATMA
    if "kendini geliştir" in query or "sisteme özellik ekle" in query or "kodunu güncelle" in query:
        self_improvement_state = {"active": True, "description": ""}
        return "Kişisel gelişim protokolü başlatıldı efendim. Ne istersiniz?"

    # 10. PROJE MODU (Aktifse)
    if project_creation_state["active"]:
        if "iptal" in query or "vazgeç" in query:
            project_creation_state = {"active": False, "step": 0, "folder_name": "", "description": ""}
            return "Proje oluşturma modu kapatıldı efendim."
        
        if project_creation_state["step"] == 0:
            folder_name = query.replace("olsun", "").replace("ismi", "").strip().lower().replace(" ", "-")
            project_creation_state["folder_name"] = folder_name
            project_creation_state["step"] = 1
            return f"Anlaşıldı efendim, proje ismi '{folder_name}' olarak belirlendi. Detayları alabilir miyim?"
        
        elif project_creation_state["step"] == 1:
            user_input = query.strip().lower()
            if any(k in user_input for k in ["tamamdır", "bu kadar", "hazır", "başla", "tamam"]):
                description = project_creation_state["description"]
                folder_name = project_creation_state["folder_name"]
                
                if not description:
                    return "Efendim, henüz herhangi bir detay vermediniz."

                new_project_path = os.path.join(TARGET_DIR, folder_name)
                if not os.path.exists(new_project_path):
                    os.makedirs(new_project_path)
                
                from ai_brain import generate_gemini_prompt
                ai_output = generate_gemini_prompt(description)
                
                try:
                    detailed_prompt = [l for l in ai_output.split("\n") if "PROMPT:" in l][0].split("PROMPT:")[1].strip()
                except:
                    detailed_prompt = description

                run_gemini_integrated(new_project_path, detailed_prompt, folder_name)
                project_creation_state = {"active": False, "step": 0, "folder_name": "", "description": ""}
                return f"Tüm talimatlarınız not edildi efendim. {folder_name} üzerinde çalışıyorum."
            else:
                project_creation_state["description"] += query + " "
                return "Not aldım. Başka bir detay?"

    # 11. PROJE MODU BAŞLATMA
    if "proje modu" in query or ("yeni" in query and "proje" in query and "başlat" in query):
        project_creation_state = {"active": True, "step": 0, "folder_name": "", "description": ""}
        return "Proje oluşturma protokolü başlatıldı. Projenin ismi ne olsun efendim?"

    return None


    return None