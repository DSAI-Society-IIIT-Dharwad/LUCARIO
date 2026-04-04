import whisper
import torch
from pyannote.audio import Pipeline
from config import WHISPER_MODEL, HF_TOKEN

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("⏳ Loading Whisper model...")
model = whisper.load_model(WHISPER_MODEL).to(device)

print("⏳ Loading Pyannote speaker diarization...")
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)
if diarization_pipeline is not None:
    diarization_pipeline.to(device)
else:
    print("❌ Failed to load Pyannote pipeline. Check your HF_TOKEN and model agreements.")

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
        
    whisper_audio = audio_data.flatten()
    
    # Pyannote expects a dictionary format for preloaded memory audio
    pyannote_audio = {
        "waveform": torch.from_numpy(audio_data).unsqueeze(0),
        "sample_rate": sample_rate
    }

    print("🗣️ Running Whisper transcription...")
    result = model.transcribe(whisper_audio, language="en", word_timestamps=True)
    
    print("🧑‍🤝‍🧑 Running speaker diarization...")
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
                
        final_output.append(f"[{assigned_speaker}] {segment['text'].strip()}")
    
    return "\n".join(final_output)