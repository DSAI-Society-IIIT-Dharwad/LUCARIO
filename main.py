from recorder import record_audio
from transcriber import transcribe_audio
from cleaner import clean_text
from summarizer import generate_summary, setup_qa_session
from pdf_generator import create_pdf_report

def run_voice_engine():
    print("🚀 Starting Voice Engine...")

    # Step 1: Record audio
    audio_file = record_audio()

    # Step 2: Transcribe
    print("\n🧠 Transcribing...")
    transcript = transcribe_audio(audio_file)

    # Step 3: Clean text
    cleaned = clean_text(transcript)

    if not cleaned.strip():
        print("\n❌ No speech or words were detected in the audio recording.")
        return

    # Step 4: Summarize
    print("📝 Generating summary...")
    summary = generate_summary(cleaned)

    # Step 5: Output
    print("\n--- TRANSCRIPTION ---\n")
    print(cleaned)

    print("\n--- SUMMARY ---\n")
    print(summary)
    
    # Step 6: Enter Interactive Loop
    try:
        chat_session = setup_qa_session(cleaned, summary)
    except Exception as e:
        print(f"❌ Failed to start Q&A session: {e}")
        chat_session = None

    print("\n" + "="*50)
    print("💬 Q&A AND EXPORT MODE")
    print("="*50)
    print("- Type 'pdf' to generate a downloadable PDF report of this meeting.")
    print("- Ask any questions about the conversation.")
    print("- Type 'exit' or 'quit' to end.\n")
    
    while True:
        try:
            query = input("Ask a question: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("Ending Session.")
                break
                
            if query.lower() == 'pdf':
                create_pdf_report(cleaned, summary)
                continue
                
            if not query:
                continue
                
            if chat_session:
                print("Thinking...")
                response = chat_session.send_message(query)
                print(f"\nVaudio AI: {response.text}\n")
            else:
                print("❌ Q&A session is unavailable.")
                
        except KeyboardInterrupt:
            print("\nEnding Session.")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    run_voice_engine()