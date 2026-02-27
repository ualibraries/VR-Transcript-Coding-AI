import re
import pandas as pd
from google.genai import types

# --- CONFIGURATION ---

# PASS 1: THE WORKER (Gemini 2.5 Lite)
# To run this pass, UNCOMMENT the 3 lines below and COMMENT OUT the Gemini 3 section
# MODEL_NAME = "gemini-2.5-flash-lite"
# OUTPUT_FILE = "Results_2.5_Lite.csv"
# AI_CONFIG = types.GenerateContentConfig(temperature=0.0, max_output_tokens=1024)

# PASS 2: THE AUDITOR (Gemini 3 Flash)
# Currently Active
MODEL_NAME = "gemini-3-flash-preview"
OUTPUT_FILE = "Results_3_Flash.csv"
AI_CONFIG = types.GenerateContentConfig(
    temperature=1.0,
    max_output_tokens=4096,
    thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_level="MEDIUM")

# --- UTILS ---
TIME_PATTERN = re.compile(r'\d{2}:\d{2}:\d{2}')
TAG_PATTERN = re.compile(r'<DATE_TIME>')
STAFF_ID_PATTERN = re.compile(r'[a-f0-9]{32,}')

def clean_raw_text(text):
    if pd.isna(text) or not isinstance(text, str): 
        return ""
    text = TIME_PATTERN.sub('', text)
    text = TAG_PATTERN.sub('', text)
    text = STAFF_ID_PATTERN.sub('STAFF', text)
    return text.strip()
