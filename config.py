import os
from dotenv import load_dotenv

load_dotenv()

AUDIO_FILE = "audio/recording.wav"
DURATION = 30
WHISPER_MODEL = "large-v2"
HF_TOKEN = os.getenv("HF_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")