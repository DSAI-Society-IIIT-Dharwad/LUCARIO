import whisper
import torch
from pyannote.audio import Pipeline
from config import WHISPER_MODEL, HF_TOKEN

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  Using device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else " (CPU — CUDA not found)"))

print("⏳ Loading Whisper model...")
model = whisper.load_model(WHISPER_MODEL).to(device)

print("⏳ Loading Pyannote speaker diarization...")
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)
if diarization_pipeline is not None:
    # Offloading to CPU to save GPU VRAM (crucial for 4GB cards)
    diarization_pipeline.to(torch.device("cpu"))
else:
    print("❌ Failed to load Pyannote pipeline. Check your HF_TOKEN and model agreements.")

import math
import numpy as np
from scipy.io import wavfile

def transcribe_audio(file_path):
    print("🗣️ Reading audio file into memory...")
    # Read audio using scipy to totally bypass the system FFmpeg requirement
    sample_rate, data = wavfile.read(file_path)
    
    # Normalizing 16-bit PCM to float32 between -1.0 and 1.0 (Whisper requirement)
    if data.dtype == np.int16:
        audio_data = data.astype(np.float32) / 32768.0
    else:
        audio_data = data.astype(np.float32)
        
    # Critically Important: Convert stereo to mono because Browser microphones often capture 2 channels
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1, dtype=np.float32)
        
    # Whisper expects a flat 1D array
    whisper_audio = audio_data.flatten()
    
    # Pyannote expects [channels, time] format
    pyannote_audio = {
        "waveform": torch.from_numpy(audio_data).unsqueeze(0),
        "sample_rate": sample_rate
    }

    print(f"🗣️ Running Whisper transcription on {device}...")
    # Removed language="en" to allow default multilingual language detection
    # condition_on_previous_text=False prevents the model from getting "stuck" in the language of the first speaker
    # Shorter, more balanced prompt to prevent English "lock-in"
    finance_prompt = "हिन्दी, தமிழ், English. Mixed language conversation about home loans, EMI, and interest rates. Please transcribe in the original languages (Devanagari for Hindi, Tamil script for Tamil, English for English)."
    
    result = model.transcribe(
        whisper_audio, 
        task="transcribe", # Explicitly ensure it's not trying to translate to English
        word_timestamps=True, 
        condition_on_previous_text=False,
        initial_prompt=finance_prompt,
        no_speech_threshold=0.6,
        fp16=True 
    )
    
    print("🧑‍🤝‍🧑 Running speaker diarization on CPU...")
    if diarization_pipeline is None:
        return result["text"]
        
    output = diarization_pipeline(pyannote_audio)
    
    # Pyannote 3.3 returns a DiarizeOutput struct instead of the raw Annotation when dealing with in-memory dicts
    diarization = output.speaker_diarization if hasattr(output, "speaker_diarization") else output
    
    print("🔗 Merging timestamps...")
    final_output = []
    
    for segment in result["segments"]:
        mid_time = (segment["start"] + segment["end"]) / 2
        assigned_speaker = "UNKNOWN"
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if turn.start <= mid_time <= turn.end:
                assigned_speaker = speaker
                break
                
        words = segment.get("words", [])
        if words:
            probs = [w.get("probability", 0.0) for w in words]
            confidence = (sum(probs) / len(probs)) * 100 if probs else 0.0
        else:
            confidence = math.exp(segment.get("avg_logprob", 0)) * 100
            
        final_output.append(f"[{assigned_speaker}] {segment['text'].strip()} (Conf: {confidence:.1f}%)")
    
    # CRITICAL: Clear GPU cache for 4GB VRAM stability
    torch.cuda.empty_cache()
    
    return "\n".join(final_output)