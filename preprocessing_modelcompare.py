import re
import pandas as pd
from google.genai import types  # Add this import at the top

# --- CONFIGURATION ---
MODELS_TO_TEST = ["gemini-2.5-flash-lite", "gemini-3-flash-preview"]

AI_CONFIG = types.GenerateContentConfig(
    temperature=1.0,
    max_output_tokens=4096,
    top_k=1,
    thinking_config=types.ThinkingConfig(
        include_thoughts=True,
        thinking_level="MEDIUM"  # Valid options: "MINIMAL", "LOW", "MEDIUM", "HIGH"
    )
)

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
    
    text = TIME_PATTERN.sub('', text)
    text = TAG_PATTERN.sub('', text)
    text = STAFF_ID_PATTERN.sub('STAFF', text)
    
    return text.strip()
