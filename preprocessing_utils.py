import re
import pandas as pd

def clean_raw_text(text):
    """
    Strips timestamps and anonymizes long alphanumeric IDs 
    to preserve context while reducing token noise.
    """
    if pd.isna(text): return ""
    # Strip clock times (00:00:00)
    text = re.sub(r'\d{2}:\d{2}:\d{2}', '', text)
    # Strip specific date/time tags
    text = re.sub(r'<DATE_TIME>', '', text)
    # Redact long alphanumeric person IDs (32+ chars) to 'STAFF'
    text = re.sub(r'[a-f0-9]{32,}', 'STAFF', text)
    return text.strip()
