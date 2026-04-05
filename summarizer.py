import google.generativeai as genai
from config import GEMINI_API_KEY
import json

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env. Skipping advanced summarization.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

HOME_SYSTEM_PROMPT = """
You are a friendly and helpful Personal Financial Assistant.
Your task is to analyze the following diarized conversation transcript (where speakers are labeled [SPEAKER_00], etc.).
Extract the key financial topics discussed and provide a clear, jargon-free summary that a general user can understand.
If you can, try to map the Speaker IDs to logical roles (e.g., Client, Financial Advisor).

Provide friendly PROACTIVE SUGGESTIONS.
If a critical component (like EMI) is unknown but Loan Amount and Interest Rate are provided, CALCULATE an estimated EMI (assume a standard 5 or 10-year tenure if tenure is missing) and explain it in simple terms.
Focus on practical next steps and financial health tips.

Respond ONLY with a valid JSON document structured exactly as follows:
{
  "financial_summary": "A simple, friendly 2-3 sentence overview of the financial discussion.",
  "extracted_data": {
    "loan_amount": "Amount if mentioned, else None",
    "interest_rate": "Rate if mentioned, else None",
    "tenure": "Tenure/duration if mentioned, else None",
    "emi": "EMI if mentioned or calculated estimate based on Amount/Rate, else None"
  },
  "speakers_identified": {
    "SPEAKER_00": "Assumed Role (e.g. Agent)",
    "SPEAKER_01": "Assumed Role (e.g. Client)"
  },
  "proactive_suggestions": [
     "Practical tip or action item for the user."
  ],
  "risk_score": 50,
  "reminders": [
     "Simple follow-up task or reminder extracted from the text."
  ]
}
"""

CORPORATE_SYSTEM_PROMPT = """
You are a senior Corporate Financial Analyst and Compliance Officer.
Your task is to analyze the following diarized conversation transcript (where speakers are labeled [SPEAKER_00], etc.) from a business or institutional financial meeting.
Extract all financial terms, obligations, and key decisions discussed. Provide a highly professional, structured summary using standard business and financial terminology.
If you can, try to map the Speaker IDs to logical roles (e.g., Relationship Manager, Corporate Client, CFO, Legal Counsel).

Apply a REGULATORY AND COMPLIANCE LENS:
- Reference applicable regulations and guidelines where relevant (e.g., RBI Master Circulars, SEBI regulations, FEMA guidelines, Companies Act 2013, IND AS/IFRS standards, Basel III norms for credit risk).
- Flag any potential compliance risks, covenant breaches, or due diligence gaps.
- If financial figures are mentioned, compute key ratios or metrics (e.g., Debt-to-Equity, DSCR, Interest Coverage Ratio) if enough data is available.
- Recommend mandatory filings, board resolutions, or statutory disclosures that may be required based on the discussion.

Provide STRATEGIC RECOMMENDATIONS grounded in corporate finance best practices:
- Highlight capital structure implications.
- Flag any interest rate risks, currency risks, or refinancing considerations.
- Suggest next steps for credit appraisal, due diligence, or term sheet preparation if applicable.

Respond ONLY with a valid JSON document structured exactly as follows:
{
  "financial_summary": "A formal, professional 2-3 sentence executive summary using business terminology.",
  "extracted_data": {
    "loan_amount": "Facility amount if mentioned, else None",
    "interest_rate": "Applicable rate / spread if mentioned, else None",
    "tenure": "Tenor/maturity if mentioned, else None",
    "emi": "Debt service obligation / installment if mentioned or calculated estimate, else None"
  },
  "speakers_identified": {
    "SPEAKER_00": "Assumed Professional Role (e.g. Relationship Manager)",
    "SPEAKER_01": "Assumed Professional Role (e.g. CFO / Corporate Client)"
  },
  "regulatory_flags": [
    "Specific regulation or compliance requirement relevant to this discussion (e.g., RBI prudential norms on large exposures, SEBI LODR obligations)."
  ],
  "proactive_suggestions": [
    "Strategic recommendation using corporate finance terminology."
  ],
  "risk_score": 50,
  "reminders": [
    "Formal action item, filing deadline, or follow-up obligation extracted from the text."
  ]
}
"""

generation_config = {
  "temperature": 0.1,
  "top_p": 0.95,
  "top_k": 64,
  "response_mime_type": "application/json",
}

def _get_model(role="Home"):
    system_prompt = CORPORATE_SYSTEM_PROMPT if role == "Corporate" else HOME_SYSTEM_PROMPT
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt,
        generation_config=generation_config
    )

def generate_summary(text, role="Home"):
    if not GEMINI_API_KEY:
        return "❌ Please add your GEMINI_API_KEY to the .env file."
    
    is_corporate = (role == "Corporate")
    print(f"📝 Sending transcript to Gemini [{role} mode] for financial extraction...")
    try:
        ai_model = _get_model(role)
        response = ai_model.generate_content(text)
        
        # Parse JSON and format it into a beautiful markdown string
        data = json.loads(response.text)
        
        if is_corporate:
            markdown_output = "## 📋 Corporate Financial Analysis Report\n\n"
            markdown_output += f"**Executive Summary:** {data.get('financial_summary', 'N/A')}\n\n"
            
            markdown_output += "### 🏦 Financial Terms & Facility Details\n"
            for key, value in data.get('extracted_data', {}).items():
                markdown_output += f"- **{key.replace('_', ' ').title()}:** {value}\n"
                
            markdown_output += "\n### 👔 Meeting Participants\n"
            for spkr, spkr_role in data.get('speakers_identified', {}).items():
                markdown_output += f"- **{spkr}:** {spkr_role}\n"
                
            reg_flags = data.get('regulatory_flags', [])
            if reg_flags:
                markdown_output += "\n### ⚖️ Regulatory & Compliance Considerations\n"
                for flag in reg_flags:
                    markdown_output += f"- {flag}\n"
                    
            suggestions = data.get('proactive_suggestions', [])
            if suggestions:
                markdown_output += "\n### 🎯 Strategic Recommendations\n"
                for sig in suggestions:
                    markdown_output += f"- {sig}\n"
        else:
            markdown_output = "## 📊 Financial Summary\n\n"
            markdown_output += f"**Overview:** {data.get('financial_summary', 'N/A')}\n\n"
            
            markdown_output += "### 🏦 Extracted Data\n"
            for key, value in data.get('extracted_data', {}).items():
                markdown_output += f"- **{key.replace('_', ' ').title()}:** {value}\n"
                
            markdown_output += "\n### 👥 Participants Identified\n"
            for spkr, spkr_role in data.get('speakers_identified', {}).items():
                markdown_output += f"- **{spkr}:** {spkr_role}\n"
                
            suggestions = data.get('proactive_suggestions', [])
            if suggestions:
                markdown_output += "\n### 💡 Proactive Suggestions\n"
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

def ask_question(transcript, summary, history, user_message, role="Home"):
    """
    Stateless Q&A — reconstructs full context on every request.
    history: list of {role: 'user'|'ai', content: str}
    """
    if not GEMINI_API_KEY:
        return "❌ Please add your GEMINI_API_KEY to the .env file."

    if role == "Corporate":
        persona = (
            "You are a senior Corporate Financial Analyst and Compliance Officer. "
            "Answer with precision using formal business and financial terminology. "
            "Reference relevant regulations (RBI, SEBI, FEMA, Companies Act, IND AS/IFRS, Basel III) where applicable. "
            "Be concise and professional. Do NOT output JSON."
        )
    else:
        persona = (
            "You are a friendly and knowledgeable Personal Financial Assistant. "
            "Answer in simple, clear language that anyone can understand. "
            "Be warm and helpful. Do NOT output JSON."
        )

    context_prompt = f"""{persona}

You are answering questions about a specific recorded financial conversation.

=== MEETING TRANSCRIPT ===
{transcript}

=== AI-EXTRACTED SUMMARY ===
{summary}

Base your answers on the meeting content provided above. If an EMI or calculation is requested and the core data is in the transcript but the calculation itself is missing, please PERFORM the calculation to be helpful. Assume a standard 10-year period if the tenure is missing.
"""

    # Build Gemini chat history: seed with context, then replay prior messages
    gemini_history = [
        {"role": "user",  "parts": [context_prompt]},
        {"role": "model", "parts": ["Understood. I have reviewed the meeting transcript and summary. I am ready to answer your questions."]}
    ]
    for msg in history:
        gemini_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [msg["content"]]
        })

    try:
        qa_model = genai.GenerativeModel("gemini-2.5-flash")
        chat = qa_model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"❌ AI error: {str(e)}"


# Keep legacy function for backward compatibility
def setup_qa_session(transcript, summary_markdown):
    if not GEMINI_API_KEY:
        return None
    qa_model = genai.GenerativeModel("gemini-2.5-flash")
    chat = qa_model.start_chat(history=[
        {"role": "user",  "parts": [f"You are a Financial Assistant for this meeting.\n\nTRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{summary_markdown}\n\nAnswer questions about this meeting in plain language. No JSON."]},
        {"role": "model", "parts": ["Understood. Ready to answer questions about this meeting."]}
    ])
    return chat