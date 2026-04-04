import os
import re
import textwrap
from fpdf import FPDF

def create_pdf_report(transcript, summary):
    print("\n📄 Saving PDF Report...")
    
    # Ensure output directory exists
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    pdf = FPDF()
    pdf.add_page()
    
    # Use standard Arial font
    pdf.set_font("Arial", size=12)
    
    # Clean up markdown and emojis that FPDF can't handle out of the box natively
    def clean_text_for_pdf(text):
        # Remove common emojis
        text = re.sub(r'[📊🏦👥💡✅❌🎙️🚀📝🧠🤝🗣️]', '', text)
        # Remove markdown bold formatting
        text = text.replace('**', '')
        # Remove headers hashes
        text = text.replace('## ', '').replace('### ', '')
        # Encode strictly to latin-1 to avoid throwing UnicodeEncodingErrors in standard Arial
        return text.encode('latin-1', 'replace').decode('latin-1')
        
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Vaudio Financial Assistant Report", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Audio Transcript", ln=True, align="L")
    pdf.set_font("Arial", size=10)
    
    for line in transcript.split('\n'):
        if line.strip():
            # Wrap text to prevent FPDF layout crashing on long contiguous strings
            wrapped = textwrap.wrap(clean_text_for_pdf(line.strip()), width=95)
            for w in wrapped:
                pdf.multi_cell(0, 6, txt=w)
            
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Financial Summary & Extraction", ln=True, align="L")
    pdf.set_font("Arial", size=10)
    
    clean_summary = clean_text_for_pdf(summary)
    for line in clean_summary.split('\n'):
        if line.strip():
            wrapped = textwrap.wrap(line.strip(), width=95)
            for w in wrapped:
                pdf.multi_cell(0, 6, txt=w)
            
    output_path = "reports/Financial_Summary.pdf"
    pdf.output(output_path)
    print(f"✅ PDF saved successfully at: {output_path}")
    return output_path
