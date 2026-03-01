import re
import pandas as pd

# --- CONFIGURATION: GEMINI 3 FLASH PREVIEW ---
# Updated to the specific Gemini 3 Flash model name
MODEL_NAME = "gemini-3-flash" # Use -preview if -flash isn't available yet

AI_CONFIG = {
    "temperature": 1.0,         # Required for Gemini 3 'Thinking' models
    "max_output_tokens": 4096, # INCREASED: Gemini 3 needs "room to think" 
    "top_k": 1, 
    "thinking_config": {
        "include_thoughts": True,
        "thinking_level": "MEDIUM" # Prevents "Infinite Loops" while maintaining depth
    }
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
    
    # 4. NEW: Normalize whitespace to reduce token count
    # This keeps the context but makes the prompt more efficient
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
