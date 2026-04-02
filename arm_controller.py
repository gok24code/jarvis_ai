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
            if any(desc in p.description for desc in ["Arduino", "CH340", "USB-SERIAL", "USB Serial"]):
                return p.device
        return "COM9"

    def _initialize_serial(self):
        try:
            if self.ser: self.ser.close()
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            self.is_connected = True
            log(f"ARM_CONTROLLER: Connected to {self.port}")
        except Exception as e:
            log(f"ARM_CONTROLLER_ERR: Could not connect to arm - {e}")
            self.is_connected = False

    def send_command(self, cmd, val=None):
        if self.is_connected and self.ser:
            with self._serial_lock:
                try:
                    msg = f"{cmd}{val}\n" if val is not None else f"{cmd}\n"
                    self.ser.write(msg.encode())
                except:
                    self.is_connected = False

    def move_base(self, angle): self.send_command('B', angle)
    def move_shoulder(self, angle): self.send_command('S', angle)
    def move_elbow_alt(self, angle): self.send_command('A', angle)
    def move_elbow_ust(self, angle): self.send_command('U', angle)
    def home(self): self.send_command('H')
    def laydown(self): self.send_command('L')
    def dogrul(self): self.send_command('D')

    def _talk_loop(self):
        pass

    def start_talking_animation(self):
        self.talking = True

    def stop_talking_animation(self):
        self.talking = False

# Singleton Instance
arm = ArmController()
