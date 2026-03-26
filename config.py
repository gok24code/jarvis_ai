import os
import pygame
from dotenv import load_dotenv
from groq import Groq
from elevenlabs.client import ElevenLabs

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Clients
client_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
client_eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

# UI Constants
COLOR_HUD = "#00f3ff"
COLOR_LISTENING = "#007bff"
COLOR_PROCESSING = "#0033ff"
HUD_WIDTH = 200
HUD_HEIGHT = 60

# System Paths
TARGET_DIR = r"C:/Users/gok2/Desktop/git"
DISCORD_PATH = r"C:\Users\gok2\AppData\Local\Discord\Update.exe"

# Initialize Pygame Mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

DEBUG = True

def log(message):
    if DEBUG:
        print(f"[SYSTEM_LOG] {message}")
