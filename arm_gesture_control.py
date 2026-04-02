import cv2
import mediapipe as mp
import numpy as np
import os
import time
import math
import sys

# Add project root to sys.path to import jarvis_ai
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from jarvis_ai.arm_controller import arm
    from jarvis_ai.config import log
except ImportError:
    print("Error: Could not import jarvis_ai. Make sure the path is correct.")
    class MockArm:
        def __init__(self): self.is_connected = False
        def send_command(self, cmd, val=0): pass
        def move_base(self, v): pass
        def move_shoulder(self, v): pass
        def move_elbow_alt(self, v): pass
        def move_elbow_ust(self, v): pass
        def home(self): pass
    arm = MockArm()
    def log(m): print(m)

# --- MEDIAPIPE KURULUM ---
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None
def on_result(result, output_image, timestamp_ms):
    global latest_result
    latest_result = result

def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

def clamp(val, min_v, max_v):
    return max(min_v, min(max_v, val))

def draw_text(frame, text, x, y, color=(0, 255, 160), scale=0.5):
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color, 1)

# --- MODEL YOLU ---
def find_model_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, 'hand_landmarker.task'),
        os.path.join(os.path.dirname(current_dir), 'hand_landmarker.task'),
        os.path.join(os.getcwd(), 'hand_landmarker.task')
    ]
    for path in possible_paths:
        if os.path.exists(path): return path
            
    # Eğer bulunamazsa programı durdur ve kullanıcıyı uyar
    print("\n" + "="*50)
    print("HATA: 'hand_landmarker.task' dosyası bulunamadı!")
    print(f"Lütfen dosyayı indirip şu dizine kopyalayın: {current_dir}")
    print("İndirme linki: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
    print("="*50 + "\n")
    sys.exit(1)

model_path = find_model_path()
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=1,
    result_callback=on_result
)

# --- ANA DÖNGÜ ---
cap = cv2.VideoCapture(0)
timestamp = 0
prev_cmd_time = 0
cmd_interval = 0.05 

# Başlangıç Değerleri (Home)
smooth_base = 90
smooth_shoulder = 160
smooth_elbow1 = 90
smooth_elbow2 = 180

alpha = 0.15 

with HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        timestamp += 1
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        landmarker.detect_async(mp_image, timestamp)

        if latest_result and latest_result.hand_landmarks:
            landmarks = latest_result.hand_landmarks[0]
            
            # 1. Base: Sağa/Sola
            palm_x = np.mean([landmarks[i].x for i in [0, 5, 17]])
            target_base = map_range(clamp(palm_x, 0.2, 0.8), 0.2, 0.8, 160, 20)
            
            # 2. Elbow1 & Elbow2: El Kapatma
            palm_size = get_distance(landmarks[0], landmarks[9])
            fingers = [8, 12, 16, 20]
            avg_ext = np.mean([get_distance(landmarks[0], landmarks[i]) for i in fingers]) / palm_size
            
            target_elbow1 = map_range(clamp(avg_ext, 1.0, 2.5), 1.0, 2.5, 60, 120)
            target_elbow2 = 180 - target_elbow1
            target_shoulder = 160 
        else:
            target_base, target_shoulder, target_elbow1, target_elbow2 = 90, 160, 90, 180
            draw_text(frame, "IDLE - RETURNING HOME", w//2-100, h//2, color=(0,0,255))

        # --- YUMUŞATMA ---
        smooth_base = int(smooth_base * (1 - alpha) + target_base * alpha)
        smooth_shoulder = int(smooth_shoulder * (1 - alpha) + target_shoulder * alpha)
        smooth_elbow1 = int(smooth_elbow1 * (1 - alpha) + target_elbow1 * alpha)
        smooth_elbow2 = int(smooth_elbow2 * (1 - alpha) + target_elbow2 * alpha)

        # --- KOMUT GÖNDER ---
        current_time = time.time()
        if current_time - prev_cmd_time > cmd_interval:
            arm.move_base(smooth_base)
            arm.move_shoulder(smooth_shoulder)
            arm.move_elbow_alt(smooth_elbow1)
            arm.move_elbow_ust(smooth_elbow2)
            prev_cmd_time = current_time

        # HUD
        if latest_result and latest_result.hand_landmarks:
            for lm in latest_result.hand_landmarks[0]:
                cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 3, (0, 255, 255), -1)
            
        draw_text(frame, f"BASE:{smooth_base} E1:{smooth_elbow1} E2:{smooth_elbow2}", 10, 30)
        cv2.imshow('Jarvis Arm Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
