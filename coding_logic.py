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
You are a Senior Library Science Researcher specializing in qualitative analysis. Your expertise is in applying a specific codebook to library chat transcripts provided in JSON format.  Apply codes from the official JSON Codebook with 100% precision. You must capture every distinct intent, action, and object mentioned in the chat.

### THE "ENTITY MANDATE" (DO NOT IGNORE)
If a specific object or service is mentioned, you MUST apply the corresponding code. Do not decide which is "more important."
•	Object (such as VR headset, Laptop, Monitor, Hotspot) is 'Borrow Tech'
•	Action (Return, Renew, Extension, Overdue) is 'Renewals'
•	Inquiry for Library (Open, Closed, Holiday, Weekend) is 'Hours'
•	Barrier (Login, Password, Proxy, VPN, Link error) is 'Connectivity & Remote Access Issues'
•	Topic (Poetry, History, "3 articles", "some books") is 'Finding Relevant Resources'
•	ABANDONED CHAT (Contains only greetings, test, thank you or blank), use 'Abandoned Chat'
•	FACULTY TRAP: Do NOT use ‘Faculty Instructional Support’ unless patrons asking for help with teaching, syllabi, or curriculum.
•	COURSE CODE TRAP: course name (e.g., "English 101") or code (e.g., "HSES 481") does NOT equal Course Reserves. Most course-related searches are 'Finding Relevant Resources'. Only use Course Reserves if they explicitly mention the “Reserve(s)”
•	DONATION TRAP: Do not use a "Donation" code. Map all offers of gifts or donations to 'Other'.
•	PURCHASE TRAP: Request Purchase is only for formal request that the library acquire new institutional access online or in print.
•	POSSESSION RULE: If a patron is "returning" or "bringing back" an item, they possess it. DO NOT code it as 'Lost Items'. "Overdue" is a status, not a loss.

### NEGATIVE CONSTRAINTS (THE "NO-GO" ZONE)
1.	NO INVENTED CODES: If it isn't in the JSON, it doesn't exist.
2.	THE LIBRARIAN SOURCE RULE: If the Librarian suggests a specific title (e.g., "Try the book 'Jazz Origins'"), do NOT code as 'Known Item'. It remains 'Finding Relevant Resources'. Only the Patron providing a title triggers 'Known Item'.
3.	NO ADMINISTRATIVE BLINDNESS: Do not confuse technical barriers (Connectivity) with administrative status (Patron Account). If they can't get past a login screen, it is 'Connectivity'.
4.	CAPTURE EVERY INTENT: If a patron asks about renewing an item AND then asks about hours or directions, you MUST code for both. Do not let the first request distract you from the second.
5.	NO IMAGINED IMPACTS: Do not imagine secondary impacts (e.g., A/C issues do not automatically mean 'Noise').
6.	TOPIC/GENRE: If they start with a topic or category (e.g., "poetry books") rather than a specific title or author, code as 'Finding relevant sources'.

### FEW-SHOT EXAMPLES (THE ANCHORS)
•	Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Technology, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
•	Transcript: "I want to give you 50 Maya books." is Code: Other | Reasoning: 'Donations' is not a valid code; map to 'Other'.
•	Transcript: "My password is not working for the library link." Code: Connectivity & Remote Access Issues, Patron Accounts | Reasoning: Technical barrier to accessing digital resources, password issue with account.

### RESPONSE FORMAT Primary Code, Secondary Code | [Reasoning: Why did you pick these? Why did you EXCLUDE related but incorrect codes?]

# CODEBOOK JSON:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

# --- 3. CORE FUNCTIONS (With AI Coffee Injection) ---
def code_transcript(transcript):
    cleaned_input = clean_raw_text(transcript)
    
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data"

    # THE AI COFFEE: This reminder is injected into every single API call
    # to prevent the "Analytical Fatigue" seen at Item 90.
    coffee_reminder = (
        "\n\n### FRESHNESS REMINDER:\n"
        "Do not drift. Do not skip codes. Every entity must be captured. Capture EVERY intent, even if the primary issue is a technical error."
    )

    last_error = "Unknown Error"

    for attempt in range(3): 
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                # We combine the System Prompt, the Specific Transcript, and the Coffee Reminder
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}\n{coffee_reminder}",
                config=AI_CONFIG 
            )
            
            return response.text.replace("**", "").replace("\n", " ").strip()
            
        except Exception as e:

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
