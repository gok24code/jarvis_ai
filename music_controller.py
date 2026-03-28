import ctypes

# Windows Virtual Key Codes
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

def send_media_key(code):
    """Windows medya tuşu sinyali gönderir."""
    ctypes.windll.user32.keybd_event(code, 0, 0, 0) # Tuşa bas
    ctypes.windll.user32.keybd_event(code, 0, 2, 0) # Tuşu bırak

class MediaController:
    def play_pause(self):
        send_media_key(VK_MEDIA_PLAY_PAUSE)
        return "Müzik durumu değiştirildi."

    def next_track(self):
        send_media_key(VK_MEDIA_NEXT_TRACK)
        return "Sıradaki parçaya geçiliyor."

    def previous_track(self):
        send_media_key(VK_MEDIA_PREV_TRACK)
        return "Önceki parçaya dönülüyor."

    def stop(self):
        send_media_key(VK_MEDIA_STOP)
        return "Oynatma durduruldu."

# Singleton instance
media_controller = MediaController()
