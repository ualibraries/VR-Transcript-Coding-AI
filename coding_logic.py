from google import genai  # Upgraded SDK
import pandas as pd
import time
import json
import os
import sys
from google.colab import userdata

# Ensure Colab finds your utility file
sys.path.append(os.getcwd())
from preprocessing_utils import clean_raw_text 

# --- BRIDGE 1: LOAD THE CODEBOOK ---
with open('codebook.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

# --- 1. CONFIGURATION ---
# The new Client is the "Boss" of your API connection
client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

INPUT_FILE = "test3_Transcripts.csv"
OUTPUT_FILE = "coded_results_pilot.csv"
MAX_ROWS = 100
SAVE_INTERVAL = 10 

# --- 2. THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
Role: Senior Library Science Researcher.
Task: Multi-label coding of transcripts using ONLY the provided JSON.
# CODING PROTOCOL:
 # PILLAR 1: THE CLOSED-LIST RULE (Discipline)
- NO INVENTED CODES: Use ONLY keys from the JSON. You are legally barred from inventing codes.
- If a concept is "good" but not in the JSON, you MUST map it to the closest existing category or use 'Other'.
 # PILLAR 2: PRIMARY INTENT (The "Kitchen Sink" Fix)
- Only code for the patron's actual NEED.
- Ignore "Atmospheric Keywords." If they say "I'm in the library (Navigation) looking at the website (Website) to find a book (Books)," the ONLY code is 'Books'.
 # PILLAR 3: REASONING AS AUDIT (The "Gem" Intuition)
- Use the reasoning section to explain why you chose a specific category over a similar one. This captures the "insight" you want without breaking the codebook.
KEYWORD CONTEXTUALIZATION: Map keywords to Intent and Definition. Do not infer meaning

3. MULTI-LABELING: Assign ALL relevant codes if a transcript touches multiple topics. Separate with commas
4. ABANDONED CHAT LOGIC (STRICT):
- Code as 'Abandoned Chat' if field is blank, [empty], or exclusively greetings ("hi", "hello")
- THRESHOLD RULE: If only content is "library help" or "library chat service" with no other nouns/verbs, code as 'Abandoned Chat'
- DO NOT code as Abandoned if second layer of intent exists (e.g., "login question")
5. EXCLUSION: Ignore system tags like <url> or <person>
6. CONSTRAINT: No prose or summaries. Process every ID individually

# OUTPUT FORMAT:
Code1, Code2 | Brief reasoning (1 sentence).

# CODEBOOK JSON:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

# --- 3. CORE FUNCTIONS ---
def code_transcript(transcript):
    cleaned_input = clean_raw_text(transcript)
    
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data"

    last_error = "Unknown Error"

    # We increased attempts and added a smarter wait time (Backoff)
    for attempt in range(3): 
        try:
            # NEW SYNTAX for the Upgraded SDK
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}"
            )
            return response.text.replace("**", "").replace("\n", " ").strip()
            
        except Exception as e:
            last_error = str(e)
            if "503" in last_error:
                # Exponential wait: 5s, 15s, 30s
                wait_time = (attempt + 1) * 10 
                print(f"⚠️ Server Busy (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                time.sleep(2)
            
    return f"ERROR | {last_error[:50]}"
   
# --- 4. MAIN EXECUTION LOOP ---
def main():
    # ... [Logic to load/resume remains same] ...
    # (Fixes the indentation error from your previous version)
    try:
        for i, row in df.iterrows():
            if processed_this_session >= MAX_ROWS: 
                break 
            
            if pd.notnull(df.at[i, 'Applied_Code_Reasoning']) and str(df.at[i, 'Applied_Code_Reasoning']).strip() != "":
                continue

            result = code_transcript(row['OriginalTranscript'])
            df.at[i, 'Applied_Code_Reasoning'] = result
            processed_this_session += 1

            if processed_this_session % 50 == 0:
                print(f"✔️ Progress: {i+1} scanned | {processed_this_session} coded")

            if processed_this_session % SAVE_INTERVAL == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                print(f"💾 Auto-save complete at row {i+1}")

            time.sleep(1.0) # Slightly longer pause for stability

    except KeyboardInterrupt:
        print("\nManual stop detected.")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nBatch complete. Total: {processed_this_session}")

if __name__ == "__main__":
    main()
