import re
import pandas as pd

# --- CONFIGURATION ---
MODEL_NAME = "gemini-2.5-flash-lite"

AI_CONFIG = {
    "temperature": 0.0,
    "top_p": 0.95,
    "max_output_tokens": 1024,
    "top_k": 1, 
}

# Pre-compiling regex for performance
TIME_PATTERN = re.compile(r'\d{2}:\d{2}:\d{2}')
TAG_PATTERN = re.compile(r'<DATE_TIME>')
STAFF_ID_PATTERN = re.compile(r'[a-f0-9]{32,}')

def clean_raw_text(text):
    """
    Cleans raw transcript text while preserving 'Semantic Anchors'.
    """
    if pd.isna(text) or not isinstance(text, str): 
        return ""
    
    # 1. Strip clock times
    text = TIME_PATTERN.sub('', text)
    # 2. Strip specific <DATE_TIME> tags
    text = TAG_PATTERN.sub('', text)
    # 3. Redact long alphanumeric IDs to 'STAFF'
    text = STAFF_ID_PATTERN.sub('STAFF', text)
    
    return text.strip()
