import sounddevice as sd
from scipy.io.wavfile import write
from config import AUDIO_FILE, DURATION

def record_audio():
    print("🎙️ Recording... Speak now!")

    fs = 16000
    # Added dtype='int16' to ensure standard PCM wav formatting. 
    # Default float32 can sometimes cause read errors or silent audio issues.
    audio = sd.rec(int(DURATION * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    write(AUDIO_FILE, fs, audio)

    print(f"✅ Recording saved as {AUDIO_FILE}")
    return AUDIO_FILE