import torch
import warnings
warnings.filterwarnings("ignore")
from pyannote.audio import Pipeline
from config import HF_TOKEN

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=HF_TOKEN)
out = pipeline({"waveform": torch.zeros(1, 16000), "sample_rate": 16000})

print("TYPE:", type(out))
print("DIR:", dir(out))
