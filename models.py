from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    raw_transcript = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_transcript": self.raw_transcript,
            "summary": self.summary,
            "risk_score": self.risk_score
        }

class Reminder(db.Model):
    __tablename__ = 'reminder'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "text": self.text
        }
