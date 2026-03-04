import pandas as pd
import re
from datetime import datetime

# 1. Configuration & Patterns
# Matches HH:MM:SS (e.g., 10:43:48)
TIMESTAMP_PATTERN = re.compile(r'(\d{1,2}:\d{2}:\d{2})')
FILE_PATH = "/content/drive/MyDrive/Colab_Outputs/Adjudication_Complete.csv"
OUTPUT_PATH = "/content/drive/MyDrive/Colab_Outputs/Reference_Intensity_Final_Sample.csv"

def get_duration_from_text(text):
    """Extracts first and last timestamp to calculate duration in seconds."""
    if pd.isna(text) or not isinstance(text, str):
        return 0
    
    matches = TIMESTAMP_PATTERN.findall(text)
    if len(matches) < 2:
        return 0 
    
    try:
        # Convert strings to datetime objects
        fmt = '%H:%M:%S'
        start = datetime.strptime(matches[0], fmt)
        end = datetime.strptime(matches[-1], fmt)
        
        # Calculate delta (handles midnight wrap-around)
        duration = (end - start).total_seconds()
        if duration < 0:
            duration += 86400
        return duration
    except:
        return 0

# 2. Load and Process
df = pd.read_csv(FILE_PATH)

# --- A. TIME & STRUCTURE METRICS ---
df['Duration_Seconds'] = df['Transcript'].apply(get_duration_from_text)
df['Word_Count'] = df['Transcript'].apply(lambda x: len(str(x).split()))

# --- B. AI INTENT METRICS ---
# Count codes in 'New_AI_Final_Code' (e.g., "Code1, Code2" = 2)
df['AI_Code_Count'] = df['New_AI_Final_Code'].apply(
    lambda x: len([c.strip() for c in str(x).split(',') if c.strip()]) if pd.notna(x) else 0
)

# --- C. INTENSITY SCORING ---
# Avoid division by zero for very short or broken transcripts
df_clean = df[df['Duration_Seconds'] > 10].copy() 

# Intensity = Codes per 10 minutes of active chat
df_clean['Intensity_Score'] = (df_clean['AI_Code_Count'] / df_clean['Duration_Seconds']) * 600

# 3. Categorize by "Reference Type"
def label_intensity(row):
    if row['Duration_Seconds'] > 900 and row['AI_Code_Count'] >= 3:
        return "Deep Research (High Time / High Intent)"
    if row['Duration_Seconds'] < 300 and row['AI_Code_Count'] >= 3:
        return "High Intensity Sprint (Low Time / High Intent)"
    if row['Duration_Seconds'] > 900 and row['AI_Code_Count'] <= 1:
        return "Verbose Simple (High Time / Low Intent)"
    return "Standard Reference"

df_clean['Reference_Profile'] = df_clean.apply(label_intensity, axis=1)

# 4. Save Results
df_clean.to_csv(OUTPUT_PATH, index=False)

print(f"✅ Intensity Analysis Complete for {len(df_clean)} rows.")
print(f"📊 Avg Duration: {df_clean['Duration_Seconds'].mean()/60:.2f} minutes")
print(f"🚀 High Intensity Sprints Found: {len(df_clean[df_clean['Reference_Profile'] == 'High Intensity Sprint (Low Time / High Intent)'])}")
