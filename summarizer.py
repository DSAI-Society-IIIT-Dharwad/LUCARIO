import google.generativeai as genai
from config import GEMINI_API_KEY
import json

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env. Skipping advanced summarization.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are a highly professional Financial Assistant. 
Your task is to analyze the following diarized conversation transcript (where speakers are labeled [SPEAKER_00], etc.).
You must extract the exact financial terms discussed and provide a professional summary format.
If you can, try to map the Speaker IDs to logical roles (e.g., Client, Financial Advisor).

Crucially, you must provide PROACTIVE SUGGESTIONS. 
If a critical component (like EMI) is unknown but Loan Amount and Interest Rate are provided, ACTUALLY CALCULATE an estimated EMI (assume a standard 5 or 10-year tenure if tenure is missing) and provide it in the suggestions. Identify any missing documents or next steps based on the context.

Respond ONLY with a valid JSON document structured exactly as follows:
{
  "financial_summary": "A polished 2-3 sentence overview of the financial discussion.",
  "extracted_data": {
    "loan_amount": "Amount if mentioned, else None",
    "interest_rate": "Rate if mentioned, else None",
    "tenure": "Tenure/duration if mentioned, else None",
    "emi": "EMI if mentioned, else None"
  },
  "speakers_identified": {
    "SPEAKER_00": "Assumed Role (e.g. Agent)",
    "SPEAKER_01": "Assumed Role (e.g. Client)"
  },
  "proactive_suggestions": [
     "Suggestion 1: Calculate the missing EMI here if possible."
  ],
  "risk_score": 50,
  "reminders": [
     "Specific task or follow-up date extracted from text."
  ]
}
"""

generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 64,
  "response_mime_type": "application/json",
}

if GEMINI_API_KEY:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=generation_config
    )

def generate_summary(text):
    if not GEMINI_API_KEY:
        return "❌ Please add your GEMINI_API_KEY to the .env file."
        
    print("📝 Sending transcript to Gemini for financial extraction...")
    try:
        response = model.generate_content(text)
        
        # Parse JSON and format it into a beautiful markdown string
        data = json.loads(response.text)
        
        markdown_output = "## 📊 Professional Financial Summary\n\n"
        markdown_output += f"**Overview:** {data.get('financial_summary', 'N/A')}\n\n"
        
        markdown_output += "### 🏦 Extracted Data\n"
        for key, value in data.get('extracted_data', {}).items():
            markdown_output += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            
        markdown_output += "\n### 👥 Participants Identified\n"
        for spkr, role in data.get('speakers_identified', {}).items():
            markdown_output += f"- **{spkr}:** {role}\n"
            
        suggestions = data.get('proactive_suggestions', [])
        if suggestions:
            markdown_output += "\n### 💡 Proactive Suggestions (AI Insights)\n"
            for sig in suggestions:
                markdown_output += f"- {sig}\n"
            
        risk_score = data.get('risk_score', 0)
        reminders = data.get('reminders', [])
        
        return {
            "summary": markdown_output,
            "risk_score": risk_score,
            "reminders": reminders
        }
        
    except Exception as e:
        return {"summary": f"❌ Failed to parse response: {str(e)}\n\nPlease ensure your API key has quota and access.", "risk_score": 0, "reminders": []}

def setup_qa_session(transcript, summary_markdown):
    if not GEMINI_API_KEY:
        return None
        
    chat_prompt = f"""
    You are a Financial Assistant handling questions about the following meeting.
    
    TRANSCRIPT:
    {transcript}
    
    AI EXTRACTED DATA:
    {summary_markdown}
    
    Use this information to answer any follow-up questions from the user regarding this specific meeting.
    Please answer strictly in plain, conversational language (DO NOT output JSON blocks). Provide thoughtful analysis.
    """
    
    qa_model = genai.GenerativeModel("gemini-2.5-flash")
    
    chat = qa_model.start_chat(history=[
        {"role": "user", "parts": [chat_prompt]},
        {"role": "model", "parts": ["Understood. I am ready to answer questions regarding this meeting."]}
    ])
    
    return chat