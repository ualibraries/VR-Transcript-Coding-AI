import re
import pandas as pd
from google.genai import types # Moved to top

# --- CONFIGURATION ---
# Define your "Scientific Constants" here
from google.genai import types  # Use the new unified types

MODEL_NAME = "gemini-2.5-flash-lite"

# Using a Dictionary is the safest way to avoid 'AttributeError' across versions
AI_CONFIG = {
    "temperature": 0.0,
    "top_p": 0.95,
    "max_output_tokens": 1024,
    "top_k": 1,  # Recommended for high-consistency research coding
}

# --- CLEANING LOGIC ---
def clean_raw_text(text):
    if pd.isna(text): 
        return ""
    
    # 1. Strip clock times (e.g., 14:02:55)
    text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
    
    # 2. Strip specific <DATE_TIME> tags
    text = re.sub(r'<DATE_TIME>', '', text)
    
    # 3. Redact long alphanumeric IDs to 'STAFF' 
    # (Matches 32+ char hex strings common in chat logs)
    text = re.sub(r'[a-f0-9]{32,}', 'STAFF', text)
    
    return text.strip()
