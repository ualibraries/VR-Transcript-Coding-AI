import google.generativeai as genai
import pandas as pd
import time
import json
import os
from google.api_core import exceptions
from google.colab import userdata

# --- BRIDGE 1: IMPORT YOUR UTILITY ---
# This looks for preprocessing_utils.py in the same folder
from preprocessing_utils import clean_raw_text 

# --- BRIDGE 2: LOAD THE CODEBOOK ---
with open('codebook.json', 'r') as f:
    # Since there is no top-level key, the whole file IS the dictionary
    CODEBOOK_DICT = json.load(f)

# This stays the same
VALID_CODES = set(CODEBOOK_DICT.keys())

# --- 1. CONFIGURATION ---
API_KEY = userdata.get('GEMINI_API_KEY')
INPUT_FILE = "test3_Transcripts.csv"
OUTPUT_FILE = "coded_results_pilot.csv"
MAX_ROWS = 100
SAVE_INTERVAL = 10 

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

VALID_CODES = set(CODEBOOK_DICT.keys())

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
    # This now uses the function we imported from preprocessing_utils
    cleaned_input = clean_raw_text(transcript)
    
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data"

    last_error = "Unknown Error" # Initialize the variable

    for attempt in range(2): 
        try:
            response = model.generate_content(
                f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}",
                generation_config={"temperature": 0.0}
            )
            return response.text.replace("**", "").replace("\n", " ").strip()
        except Exception as e:
            last_error = str(e) # Store the error message
            time.sleep(2) # Wait before trying again
            
    # If we get here, both attempts failed
    return f"ERROR | {last_error[:50]}"
   
# --- 4. MAIN EXECUTION LOOP ---
def main():
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from {OUTPUT_FILE}...")
        df = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"Starting fresh from {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE)

    if 'Applied_Code_Reasoning' not in df.columns:
        df['Applied_Code_Reasoning'] = ""

    total_rows = len(df)
    processed_this_session = 0

    print(f"Beginning processing of {total_rows} rows...")

    try:
        for i, row in df.iterrows():
            if processed_this_session >= MAX_ROWS: break # Respect the MAX_ROWS limit
            
            if pd.notnull(df.at[i, 'Applied_Code_Reasoning']) and df.at[i, 'Applied_Code_Reasoning'] != "":
                continue

            # Ensure 'OriginalTranscript' matches your CSV header exactly
            result = code_transcript(row['OriginalTranscript'])
            df.at[i, 'Applied_Code_Reasoning'] = result

            processed_this_session += 1

            if processed_this_session % 10 == 0:
                print(f"Progress: {i+1}/{total_rows} rows completed...")

            if processed_this_session % SAVE_INTERVAL == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                print(f"--- Intermediate save at row {i+1} ---")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nManual stop detected. Saving progress...")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nBatch complete. Total session count: {processed_this_session}")

if __name__ == "__main__":
    main()
