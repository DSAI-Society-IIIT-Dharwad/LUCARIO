# Vaudio — AI-Powered Financial Conversation Assistant

> **Vaudio** is a full-stack AI web application that records or uploads spoken financial conversations, transcribes them with speaker diarization, and uses the **Google Gemini API** to extract key financial data, generate structured summaries, assess risk, and enable real-time Q&A — all in a persistent, role-aware interface.

---

## Features

| Feature | Description |
|---|---|
| **Audio Transcription** | Upload `.wav` audio files; transcribed using OpenAI Whisper (medium model), bypassing FFmpeg via `scipy` |
| **Speaker Diarization** | Identifies individual speakers using `pyannote/speaker-diarization-3.1` with confidence scores |
| **AI Financial Analysis** | Google Gemini 2.5 Flash extracts loan amount, interest rate, tenure, EMI, and generates structured summaries |
| **Dual Modes** | **Home mode** for personal finance (friendly, jargon-free) and **Corporate mode** for institutional analysis (formal, with regulatory references) |
| **Risk Scoring** | Gemini assigns a risk score (0–100) to every conversation |
| **Automated Reminders** | AI extracts follow-up action items and reminders from the conversation |
| **Editable Transcripts** | Users can edit transcripts post-transcription; the summary is automatically re-generated |
| **AI Chatbot (Q&A)** | Ask follow-up questions about any saved conversation using a context-aware Gemini-powered chat |
| **Conversation History** | All sessions are persisted in SQLite and browsable by role (Home / Corporate) |
| **TXT & PDF Export** | Export any report as a plain-text `.txt` file or a formatted PDF via `fpdf` |

---

## Architecture

```
vaudio/
├── app.py                    # Flask application entry point, routes & API
├── config.py                 # Environment configuration (Whisper model, API keys, paths)
├── main.py                   # Standalone CLI runner (non-web usage)
├── requirements.txt          # Python dependencies
│
├── app/
│   ├── models/
│   │   └── models.py         # SQLAlchemy ORM: Conversation & Reminder tables
│   ├── services/
│   │   ├── transcriber.py    # Whisper + Pyannote diarization pipeline
│   │   ├── summarizer.py     # Gemini-powered summarization & Q&A
│   │   ├── cleaner.py        # Text sanitization
│   │   ├── pdf_generator.py  # FPDF-based PDF report generation
│   │   └── recorder.py       # (Optional) Local audio recording helper
│   └── templates/
│       ├── dashboard.html    # Main SPA dashboard (transcribe, history, chatbot)
│       └── login.html        # Role selection login page
│
├── audio/                    # Temporary audio file storage
├── reports/                  # Generated PDF reports
├── data/                     # Miscellaneous data files
└── instance/
    └── vaudio.db             # SQLite database (auto-created on first run)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask, Flask-SQLAlchemy |
| **Database** | SQLite (via SQLAlchemy ORM) |
| **Transcription** | OpenAI Whisper (`medium` model) |
| **Diarization** | Pyannote Audio 3.1 (`pyannote/speaker-diarization-3.1`) |
| **AI Analysis** | Google Gemini 2.5 Flash (`google-generativeai`) |
| **Audio Processing** | SciPy, NumPy (FFmpeg-free) |
| **PDF Export** | fpdf2 |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JavaScript |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A CUDA-capable GPU is recommended for faster Whisper inference (CPU works too)
- A [Hugging Face account](https://huggingface.co/) with access to `pyannote/speaker-diarization-3.1`
- A [Google AI Studio](https://aistudio.google.com/) account with a Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/DSAI-Society-IIIT-Dharwad/LUCARIO.git
cd LUCARIO
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** PyTorch with CUDA support is recommended. If not already installed with CUDA, visit [pytorch.org](https://pytorch.org/get-started/locally/) and install the appropriate version first.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
HF_TOKEN=your_huggingface_token_here
```

- **`GEMINI_API_KEY`** — Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **`HF_TOKEN`** — Get from [Hugging Face settings](https://huggingface.co/settings/tokens); you must also accept the model license at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)

### 5. Run the Application

```bash
python app.py
```

The app will start on **http://localhost:5000**. The Whisper and Pyannote models will be downloaded on the first run (~1–2 GB).

---

## Usage

### Login

Navigate to `http://localhost:5000`. Select your mode:
- **Home** — Personal financial assistant (simple, friendly language)
- **Corporate** — Institutional financial analyst (formal language with regulatory references)

### Transcribe a Conversation

1. Upload a `.wav` audio file from the dashboard.
2. Vaudio transcribes the audio, identifies speakers, and sends the transcript to Gemini.
3. The AI generates a structured financial summary, risk score, and follow-up reminders.

### Edit & Re-analyze

Click the **Edit Transcript** button on any result to correct the transcript. The summary and reminders will be automatically re-generated.

### Chat with the AI

Use the **Chat** panel to ask follow-up questions about any conversation stored in history. The AI has full context of the transcript and summary.

### Export Report

- Click **Download TXT** to save a plain-text report.
- Click **Download PDF** to download a professionally formatted PDF report.

### History Tab

Browse all past conversations for your current role, view their summaries, risk scores, and reminders.

---

## Configuration (`config.py`)

| Variable | Default | Description |
|---|---|---|
| `AUDIO_FILE` | `audio/recording.wav` | Path where uploaded audio is temporarily stored |
| `DURATION` | `30` | Max recording duration (seconds) for live recording |
| `WHISPER_MODEL` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `HF_TOKEN` | `.env` | Hugging Face API token for pyannote |
| `GEMINI_API_KEY` | `.env` | Google Gemini API key |

---

## Database Schema

### `Conversation`
| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Unique conversation ID |
| `timestamp` | DateTime | Auto-set on creation (UTC) |
| `raw_transcript` | Text | Cleaned, diarized transcript |
| `summary` | Text | Gemini-generated markdown summary |
| `risk_score` | Integer | Financial risk score (0–100) |
| `role` | String | `Home` or `Corporate` |

### `Reminder`
| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Unique reminder ID |
| `conversation_id` | Integer (FK) | Linked conversation |
| `text` | String | Action item / reminder text |
| `created_at` | DateTime | Auto-set on creation |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Redirects to `/login` or `/dashboard` |
| `GET/POST` | `/login` | Role selection login page |
| `GET` | `/logout` | Clears session and redirects to login |
| `GET` | `/dashboard` | Main application dashboard |
| `POST` | `/api/transcribe` | Upload audio, transcribe, summarize, and persist |
| `POST` | `/api/update_transcript` | Edit transcript and re-generate summary |
| `POST` | `/api/download_txt` | Download a `.txt` report |
| `GET` | `/api/history` | Fetch conversation history for current role |
| `POST` | `/api/chat` | Chat with AI about a specific conversation |

---

## Supported Audio Formats

Vaudio processes audio files using `scipy.io.wavfile`, which expects **standard WAV files**:
- **Encoding:** PCM 16-bit (most common)
- **Channels:** Mono or Stereo (stereo is automatically converted to mono)
- **Sample Rate:** Any (Whisper handles resampling internally)

> For other formats (MP3, M4A, OGG, etc.), convert to WAV first using a tool like Audacity or ffmpeg.

---

## Security Notes

- This application is designed as a **single-user local sandbox**. It does **not** implement multi-user authentication or authorization.
- The `secret_key` in `app.py` should be moved to `.env` for any non-local deployment.
- Audio files are stored temporarily and overwritten on each upload.

---

## Contributing

Contributions are welcome! Please open an issue to discuss your ideas before submitting a pull request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request

---

## License

This project was developed by the **DSAI Society, IIIT Dharwad**.

---

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — Speech-to-text transcription
- [Pyannote Audio](https://github.com/pyannote/pyannote-audio) — Speaker diarization
- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI financial analysis & Q&A
- [fpdf2](https://py-pdf.github.io/fpdf2/) — PDF generation
