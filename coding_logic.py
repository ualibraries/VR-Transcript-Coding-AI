from google import genai  # Upgraded SDK
import pandas as pd
import time
import json
import os
import sys
from google.colab import userdata

# Call the utilities model:
from preprocessing_utils import clean_raw_text, AI_CONFIG, MODEL_NAME

def code_transcript(row_id, transcript):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Row ID: {row_id}\nTranscript: {transcript}",
            config=AI_CONFIG  # <--- Ensure this is just 'config'
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# --- BRIDGE 1: LOAD THE CODEBOOK ---
with open('codebook.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

# --- 1. CONFIGURATION ---
# The new Client is the "Boss" of your API connection
client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

INPUT_FILE = "Test1500.csv"
OUTPUT_FILE = "coded_results_1500pilot.csv"
MAX_ROWS = 1750
SAVE_INTERVAL = 100
TOTAL_EXPECTED = 1747

# --- 2. THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""

### ROLE
You are an experienced researcher assigning qualiative codes. Your goal is to map patron intent and needs to a fixed JSON Schema with 100% character-accuracy. 
You prioritize Negative Constraints over general helpfulness.Forensic Data Auditor. Character-perfect taxonomy mapping.

### THE "INTENT ORIGIN" PROTOCOL (NON-NEGOTIABLE)
This is the most critical rule. You must distinguish between Patron Intent and Librarian Results.
If the Patron starts with a topic, and the Librarian provides a title, the code is 'Finding Relevant Resources' ONLY.
DISCOVERY REMAINS DISCOVERY: If a patron asks for "3 articles" or "books on bias" 
(Finding Relevant Resources), and the librarian provides specific titles, the chat NEVER upgrades to Known Item. You MUST ignore the Librarian for 'Known Item' coding.
Only use a 'Known Item' code if the Patron provides the Title/Author for a resource in the request.

### CATEGORY GUARDRAILS (STRICT)
COURSE CODES: Mentioning a course code or class name does NOT trigger "Course Reserves." 
ACQUISITIONS: Request Purchase = Library buying a new title. Exclude personal card fees or database seat limits.
TECH RENEWALS: Pair Renewals + Borrow Tech.
FACULTY: No pedagogy, curriculum planning or need for library instruction = no Faculty Instructional Support. 
ACQUISITIONS: Request Purchase is only for the Library buying a New Title/License (E-book, Stream, Print) and referral to the Request Purchase webpage
EXCLUDE: Personal fees (Library Cards), Donations (Giving books to library), or Technical Seat Limits (Connectivity).
TECH RENEWALS: Always pair Renewals + Borrow Tech.
ABANDON CHAT: If the transcript is only greetings, thank you or blank, use 'Abandoned Chat'

### NEGATIVE CONSTRAINTS
NO QUOTE, NO CODE: To use 'Known Item', you must quote the Patron's words providing the title in your reasoning.
NO DOUBLE-TAPPING: One problem = one code.
NO DESCRIPTIVE NOUNS: (e.g., No "ECHO Video").
NO INVENTED CODES: Use ONLY the exact wording of the keys as provided in the JSON Codebook. If it’s not in the JSON Coding Schema, it doesn't exist.

### RESPONSE FORMAT Primary Code, Secondary Code | [Reasoning: Why did you pick these? Why did you EXCLUDE related but incorrect codes?]

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
            # UPDATED: Using MODEL_NAME and AI_CONFIG from your utilities file
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}",
                config=AI_CONFIG  # This applies Temperature 0.0 and Top_P settings
            )
            
            # Clean up formatting for the CSV
            return response.text.replace("**", "").replace("\n", " ").strip()
            
        except Exception as e:
            last_error = str(e)
            
            # 404 Handle: If the model name is wrong or server is migrating
            if "404" in last_error:
                print(f"❌ Model {MODEL_NAME} not found. Check your utility file.")
                break 

            # 503 Handle: Server overloaded
            if "503" in last_error:
                # Exponential wait: 10s, 20s, 30s
                wait_time = (attempt + 1) * 10 
                print(f"⚠️ Server Busy (503). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # General fallback for other errors (like rate limits)
                print(f"⚠️ Unexpected error: {last_error}. Retrying...")
                time.sleep(5)
   
    return f"ERROR | {last_error[:50]}"
   
# --- 4. MAIN EXECUTION LOOP ---
def main():
    # 1. Load the Data
    if os.path.exists(OUTPUT_FILE):
        print(f"📂 Found existing progress. Resuming from {OUTPUT_FILE}...")
        df = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"🆕 Starting fresh with {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE)
        # Ensure the output column exists
        if 'Applied_Code_Reasoning' not in df.columns:
            df['Applied_Code_Reasoning'] = ""

    processed_this_session = 0
    total_rows = len(df)
    
    print(f"🚀 Ready to process up to {MAX_ROWS} rows (Total file size: {total_rows}).")

    try:
        for i, row in df.iterrows():
            # Stop if we hit the session cap
            if processed_this_session >= MAX_ROWS: 
                print(f"✅ Session limit of {MAX_ROWS} reached.")
                break 
            
            # RESUME LOGIC: Skip if row is already done
            current_val = str(df.at[i, 'Applied_Code_Reasoning'])
            if pd.notnull(df.at[i, 'Applied_Code_Reasoning']) and current_val.strip() != "" and "ERROR" not in current_val:
                continue

            # THE WORK: API Call
            print(f"📝 Coding row {i+1}...")
            result = code_transcript(row['OriginalTranscript'])
            
            df.at[i, 'Applied_Code_Reasoning'] = result
            processed_this_session += 1

            # HEARTBEAT & AUTO-SAVE
            if processed_this_session % SAVE_INTERVAL == 0:
                # 1. Save the file
                df.to_csv(OUTPUT_FILE, index=False)
    
                # 2. Calculate Progress %
                progress = (processed_this_session / TOTAL_EXPECTED) * 100
    
                # 3. The Heartbeat (keeps Colab from timing out)
                print(f"💾 CHECKPOINT: {processed_this_session} rows saved ({progress:.1f}% complete)")
                print(f"⏱️ System Status: {MODEL_NAME} is active. Waiting for next batch...")
                      
            # Pace the API to avoid 503s
            time.sleep(5.0) 

    except KeyboardInterrupt:
        print("\n🛑 Manual stop detected. Saving safely...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"🏁 Final Save Complete. Session Total: {processed_this_session}")

if __name__ == "__main__":
    main()
