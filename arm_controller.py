import serial
import serial.tools.list_ports
import threading
import time
from config import log

class ArmController:
    _instance = None
    _lock = threading.Lock()
    _serial_lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ArmController, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self.port = self._find_arduino_port()
        self.baudrate = 9600
        self.ser = None
        self.is_connected = False
        self.talking = False
        self.animation_thread = None
        self._initialize_serial()
        self._initialized = True

    def _find_arduino_port(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Yaygın Arduino/CH340 isimlerini kontrol et
            if any(desc in p.description for desc in ["Arduino", "CH340", "USB-SERIAL", "USB Serial"]):
                return p.device
        return "COM9" # Sistem logunda görünen port

    def _initialize_serial(self):
        try:
            if self.ser: self.ser.close()
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Reset sonrası bekleme
            self.is_connected = True
            log(f"ARM_CONTROLLER: Connected to {self.port}")
        except Exception as e:
            log(f"ARM_CONTROLLER_ERR: Could not connect to arm - {e}")
            self.is_connected = False

    def send_command(self, cmd, val=0):
        if self.is_connected and self.ser:
            with self._serial_lock:
                try:
                    msg = f"{cmd}{val}\n"
                    self.ser.write(msg.encode())
                except:
                    self.is_connected = False

    def move_base(self, angle): self.send_command('B', angle)
    def move_shoulder(self, angle): self.send_command('S', angle)
    def move_elbow_alt(self, angle): self.send_command('A', angle)
    def move_elbow_ust(self, angle): self.send_command('U', angle)
    def home(self): self.send_command('H')

    def _talk_loop(self):
        # Konuşma başladığında dirsekleri ayarla
        self.move_elbow_alt(60)
        self.move_elbow_ust(120)
        
        base_angle = 90
        step = 2 # Salınım hızı
        
        while self.talking:
            # Base yavaşça 45-135 arasında dönsün
            self.move_base(base_angle)
            base_angle += step
            
            if base_angle >= 135:
                step = -2
            elif base_angle <= 45:
                step = 2
                
            time.sleep(0.05)

    def start_talking_animation(self):
        if not self.talking:
            self.talking = True
            self.animation_thread = threading.Thread(target=self._talk_loop, daemon=True)
            self.animation_thread.start()

    def stop_talking_animation(self):
        self.talking = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        self.home()

# Singleton Instance
arm = ArmController()
