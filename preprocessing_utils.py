import re
import pandas as pd

def clean_raw_text(text):
    if pd.isna(text): return ""
    # Strip clock times
    text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
    # Strip <DATE_TIME> tags
    text = re.sub(r'<DATE_TIME>', '', text)
    # Redact long alphanumeric IDs to 'STAFF'
    text = re.sub(r'[a-f0-9]{32,}', 'STAFF', text)
    return text.strip()
