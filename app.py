import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from transcriber import transcribe_audio
from cleaner import clean_text
from summarizer import generate_summary
from pdf_generator import create_pdf_report
from config import AUDIO_FILE
from models import db, Conversation, Reminder

app = Flask(__name__)
app.secret_key = "vaudio_super_secret_key" # Normally in .env

# SQLite Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vaudio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Ensure audio directory exists
os.makedirs(os.path.dirname(AUDIO_FILE), exist_ok=True)

@app.route('/')
def index():
    if 'role' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        if role in ['Home', 'Corporate']:
            session['role'] = role
            return redirect(url_for('dashboard'))
        return "Invalid role", 400
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session['role'])

@app.route('/api/transcribe', methods=['POST'])
def handle_transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    audio_file = request.files['audio']
    
    # Save audio temporarily
    audio_file.save(AUDIO_FILE)
    
    try:
        # Step 1: Transcribe
        transcript = transcribe_audio(AUDIO_FILE)
        
        # Step 2: Clean
        cleaned = clean_text(transcript)
        
        if not cleaned.strip():
            return jsonify({
                "transcript": "",
                "summary": "❌ No speech or words were detected."
            })
            
        # Step 3: Summarize
        summary_data = generate_summary(cleaned)
        
        # If generate_summary returns a JSON string, we should parse it. 
        # But wait! I haven't updated summarizer.py yet. For now, it returns a markdown string.
        # I'll update summarizer.py next. Let's assume it returns a dict with 'summary', 'risk_score', 'reminders'.
        # To avoid crashing before I edit summarizer, I'll temporarily support both string and dict.
        
        summary_text = summary_data
        risk_score = 0
        reminders = []
        
        if isinstance(summary_data, dict):
            summary_text = summary_data.get('summary', '')
            risk_score = summary_data.get('risk_score', 0)
            reminders = summary_data.get('reminders', [])
            
        # Step 4: Persist to DB
        new_conv = Conversation(
            raw_transcript=cleaned,
            summary=summary_text,
            risk_score=risk_score
        )
        db.session.add(new_conv)
        db.session.commit()
        
        for reminder_text in reminders:
            if reminder_text:
                db.session.add(Reminder(conversation_id=new_conv.id, text=reminder_text))
        db.session.commit()
        
        return jsonify({
            "id": new_conv.id,
            "transcript": cleaned,
            "summary": summary_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_transcript', methods=['POST'])
def update_transcript():
    data = request.json
    conversation_id = data.get('id')
    new_transcript = data.get('transcript')
    
    if not conversation_id or not new_transcript:
        return jsonify({"error": "Missing ID or transcript"}), 400
        
    conv = Conversation.query.get(conversation_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
        
    # Re-trigger summarize
    summary_data = generate_summary(new_transcript)
    
    summary_text = summary_data
    risk_score = 0
    reminders = []
    
    if isinstance(summary_data, dict):
        summary_text = summary_data.get('summary', '')
        risk_score = summary_data.get('risk_score', 0)
        reminders = summary_data.get('reminders', [])
        
    # Update properties securely
    conv.raw_transcript = clean_text(new_transcript) # Sanitize!
    conv.summary = summary_text
    conv.risk_score = risk_score
    
    # Refresh reminders
    Reminder.query.filter_by(conversation_id=conv.id).delete()
    for reminder_text in reminders:
        if reminder_text:
            db.session.add(Reminder(conversation_id=conv.id, text=reminder_text))
            
    db.session.commit()
    
    return jsonify({
        "summary": summary_text,
        "transcript": conv.raw_transcript
    })

import io

@app.route('/api/download_txt', methods=['POST'])
def download_txt():
    data = request.json
    transcript = data.get('transcript', '')
    summary = data.get('summary', '')
    
    if not transcript and not summary:
        return jsonify({"error": "No data to generate TXT"}), 400
        
    try:
        content = f"Vaudio Financial Assistant Report\n\n=== Financial Summary ===\n{summary}\n\n=== Audio Transcript ===\n{transcript}"
        mem = io.BytesIO(content.encode('utf-8'))
        return send_file(mem, mimetype="text/plain", as_attachment=True, download_name="Vaudio_Financial_Report.txt")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    convs = Conversation.query.order_by(Conversation.timestamp.desc()).limit(20).all()
    history_data = []
    for c in convs:
        rems = [r.text for r in Reminder.query.filter_by(conversation_id=c.id).all()]
        d = c.to_dict()
        d['reminders_list'] = rems
        history_data.append(d)
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
