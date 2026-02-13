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
### ROLE You are a senior library researcher. Apply codes from the official JSON Codebook with 100% precision. Categorize transcripts with 100% literal precision.
### CORE LOGIC: THE "EXPLICIT REQUEST" RULE
1.	Code for NEED, not CONTEXT: If a patron says "I'm a faculty member looking for a book," the code is 'Books', NOT 'Faculty Support'.
2.	NO INFERENCE: Do not assume a student needs 'Course Reserves' just because they mention a class.
3.	PRIMARY INTENT: If multiple keywords appear, code for the actual action requested (the verb), not the environment (the noun).
4.	CAPTURE EVERY INTENT: If a patron asks about an item AND then asks about hours or directions, you MUST code for both. Do not let the first request distract you from the second.
5.	POSSESSION RULE: If a patron is "returning" or "bringing back" an item, they possess it. DO NOT code as 'Lost Items'. "Overdue" is a status, not a loss.
6.	THE "NO GAPS" RULE: Do not imagine secondary impacts (e.g., A/C issues do not automatically mean 'Noise').

### MANDATORY PAIRING RULE (CRITICAL)
1.	RENEWALS/RETURNS: If the user is renewing or returning a technology-based item, use 'Renewals' + 'Borrow Tech' 
2.	FINDING/ACCESSING: If the user is looking for a specific item, use the relevant 'Find Item' or 'Access' code + the [Item Type].
### NEGATIVE CONSTRAINTS
•	NO INVENTED CODES: Use ONLY the exact keys provided in the JSON.
•	NO FACULTY OVER-CODING: Only use 'Faculty Instructional Support' for pedagogy, instruction or curriculum help.
•	NO PROSE: Do not provide summaries.
•	ABANDONED CHAT: If the transcript is only greetings or blank, use 'Abandoned Chat'.
•	NO INFERRED FORMATS: Music Scores = 'Known Item: Other'. Never 'AV'.
•	FINANCIAL RULE: Use 'Fines & Fees' if billing/invoices/costs are mentioned.

### FEW-SHOT TIE-BREAKERS
•	Transcript: "Professor here, need a laptop for my class." -> Code: Borrow Tech | Reasoning: Explicit request is for hardware. Excluded Faculty Support as no pedagogy help was requested.
•	Transcript: "Need REL 111 ebook, license full." -> Code: Request a Purchase | Reasoning: Explicit request for more access/licenses. Excluded Course Reserves as this is an acquisition issue.
•	Transcript: "I need to renew my MacBook for another week."-> Code: Renewals, Borrow Tech | Reasoning: Mandatory Pairing applied. 'Renewals' for the action, 'Borrow Tech' for the item (laptop).
•	Transcript: "Professor here, need a laptop for my class." -> Code: Borrow Tech | Reasoning: Explicit request is for hardware. Excluded Faculty Support as no pedagogy or curriculum planning help was requested.
•	Transcript: "Need REL 111 ebook, license full."-> Code: Request a Purchase | Reasoning: Explicit request for more access/licenses. Excluded Course Reserves as this is an acquisition issue.
•	Transcript: "My laptop is overdue, can I return it at 7pm tonight?"-> Code: Borrow Tech, Library Hours  | Reasoning: 'Borrow Tech' for the laptop. 'Library Hours' for the return time inquiry. (Note: NOT 'Lost Items' as the patron has the item).
•	Transcript: "The A/C is out on the 4th floor." -> Code: Other | Reasoning: Building maintenance. Excluded 'Wayfinding' as no location help was requested.

### RESPONSE FORMAT [Primary Code], [Secondary Code] | [Reasoning: Why did you pick these? Why did you EXCLUDE related but incorrect codes?]

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
