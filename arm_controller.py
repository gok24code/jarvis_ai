import serial
import serial.tools.list_ports
import threading
import time
from config import log

class ArmController:
    _instance = None
    _lock = threading.Lock()

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
            if "Arduino" in p.description or "CH340" in p.description or "USB-SERIAL" in p.description:
                return p.device
        return "COM3" # Fallback

    def _initialize_serial(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Wait for Arduino reset
            self.is_connected = True
            log(f"ARM_CONTROLLER: Connected to {self.port}")
        except Exception as e:
            log(f"ARM_CONTROLLER_ERR: Could not connect to arm - {e}")
            self.is_connected = False

    def send_command(self, cmd, val=0):
        if self.is_connected:
            try:
                msg = f"{cmd}{val}\n"
                self.ser.write(msg.encode())
            except:
                self.is_connected = False

    def move_base(self, angle): self.send_command('B', angle)
    def move_shoulder(self, angle): self.send_command('S', angle)
    def move_wrist(self, angle): self.send_command('W', angle)
    def move_elbow_alt(self, angle): self.send_command('A', angle)
    def move_elbow_ust(self, angle): self.send_command('U', angle)
    def move_grip(self, angle): self.send_command('G', angle)
    def home(self): self.send_command('H')

    def _talk_loop(self):
        import random
        while self.talking:
            # Random subtle movements to look "alive" while speaking
            self.send_command('T') # Trigger arduino-side talk gesture
            time.sleep(0.5)
            # Maybe some slight wrist/shoulder adjustments
            if random.random() > 0.7:
                self.move_shoulder(random.randint(155, 165))
            if random.random() > 0.7:
                self.move_base(random.randint(85, 95))

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
