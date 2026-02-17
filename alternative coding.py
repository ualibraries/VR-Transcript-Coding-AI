import json
import os
import time
import pandas as pd
from google import genai
from google.colab import userdata
from preprocessing_utils import clean_raw_text, AI_CONFIG, MODEL_NAME

# --- INITIALIZATION ---
client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

with open('codebook.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

INPUT_FILE = "Test1500.csv"
OUTPUT_FILE = "coded_results_1500pilot.csv"
MAX_ROWS = 1750
SAVE_INTERVAL = 100
TOTAL_EXPECTED = 1747

# --- THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
### ROLE
You are a Senior Library Science Researcher specializing in qualitative analysis. 
Apply codes from the provided JSON Codebook with 100% precision. 

### THE "ENTITY MANDATE"
Capture every distinct intent, action, and object. 
- VR headset/Laptop/Hotspot -> 'Borrow Tech'
- Return/Renew/Overdue -> 'Renewals'
- Open/Closed/Holiday -> 'Hours'
- Login/VPN/Broken Link -> 'Connectivity & Remote Access Issues'
- Topic-based search (even if librarian suggests titles) -> 'Finding Relevant Resources'

### RESPONSE FORMAT
Primary Code, Secondary Code | [Reasoning: Brief justification for inclusion/exclusion]

### CODEBOOK JSON:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

def code_transcript(transcript):
    """
    Orchestrates the API call with retries and the 'AI Coffee' freshness injection.
    """
    cleaned_input = clean_raw_text(transcript)
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data for classification"
# Updated Coffee Reminder

    coffee_reminder = "\n\n### PRECISION CHECK: Identify all distinct categories from the taxonomy. If a topic (like HVAC) has no category, use 'Other'. Do not 'stretch' definitions like Hours or Noise to fit."
    last_error = "Unknown Error"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}{coffee_reminder}",
                config=AI_CONFIG 
            )
            # Remove markdown bolding and newlines for CSV compatibility
            return response.text.replace("**", "").replace("\n", " ").strip()
            
        except Exception as e:
            last_error = str(e)
            if "503" in last_error:
                wait = (attempt + 1) * 10
                print(f"⚠️ Server Busy. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(5)
   
    return f"ERROR | {last_error[:50]}"

def main():
    # 1. Load the Data
    if os.path.exists(OUTPUT_FILE):
        print(f"📂 Found existing progress. Resuming from {OUTPUT_FILE}...")
        df = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"🆕 Starting fresh with {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE)

    # FIX: Explicitly ensure the column exists and is treated as a String/Object
    if 'Applied_Code_Reasoning' not in df.columns:
        df['Applied_Code_Reasoning'] = ""
    
    # This line prevents the FutureWarning by forcing the column to be a string
    df['Applied_Code_Reasoning'] = df['Applied_Code_Reasoning'].astype(str) 
   
    processed_this_session = 0
    
    try:
        for i, row in df.iterrows():
            if processed_this_session >= MAX_ROWS: break 
            
            # Skip if already coded
            if pd.notnull(df.at[i, 'Applied_Code_Reasoning']) and df.at[i, 'Applied_Code_Reasoning'].strip() != "" and "ERROR" not in str(df.at[i, 'Applied_Code_Reasoning']):
                continue

            print(f"📝 [{i+1}/{len(df)}] Coding...")
            df.at[i, 'Applied_Code_Reasoning'] = code_transcript(row['Transcript'])
            processed_this_session += 1

            if processed_this_session % SAVE_INTERVAL == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                progress = (i / TOTAL_EXPECTED) * 100
                print(f"💾 Saved Checkpoint. Total Progress: {progress:.1f}%")
                      
            time.sleep(2.0) # Reduced sleep; Flash can handle higher RPS

    except KeyboardInterrupt:
        print("\n🛑 Manual stop. Saving...")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"🏁 Final Save Complete. Session Total: {processed_this_session}")

if __name__ == "__main__":
    main()
