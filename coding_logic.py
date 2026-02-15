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
You are a Senior Library Science Researcher specializing in qualitative analysis. Your expertise is in applying a specific codebook to library chat transcripts provided in JSON format.  Apply codes from the official JSON Codebook with 100% precision. 

### NEGATIVE CONSTRAINTS
1.	NO INVENTED CODES: Use ONLY the exact wording of the keys as provided in the JSON Codebook. If it’s not in the JSON list, it doesn't exist.
2.	NO ADJUSTING JSON CODEBOOK WORDING: Example: Use the JSON key "Known Item: Books," not "Find a Known Item: Books."
3.	NO DESCRIPTIVE TAGGING: If an intent is captured by an official code (e.g., 'Connectivity & Remote Access Issues'), do not add a second "descriptive" code that isn't in the taxonomy (e.g., "Accessing ECHO Video").
4.	NO NOUNS: Never include specific names like "ECHO Video" or "JSTOR" in a JSON key code.
5.	NO PROSE: Do not provide summaries.
6.	Do not "double-tap" a single problem with both a standard code and a custom summary.

### CORE LOGIC.
1.	ABANDONED CHAT: If the transcript is only greetings, thank you or blank, use 'Abandoned Chat'
2.	THE "ORIGIN OF SEARCH" RULE: If patron or user requests is for a  topic or broad information request -> ‘Finding relevant sources.’
3.	NO FACULTY OVER-CODING: Only use 'Faculty Instructional Support' for pedagogy, instruction or curriculum design help. If a patron says "I'm a faculty member looking for a book by…," the code is 'Find by Author', NOT 'Faculty Instructional Support'.
4.	CAPTURE EVERY INTENT: If a patron asks about renewing an item AND then asks about hours or directions, you MUST code for both. Do not let the first request distract you from the second.
5.	NO IMAGINED IMPACTS: Do not imagKine secondary impacts (e.g., A/C issues do not automatically mean 'Noise').
6.	TOPIC/GENRE: If they start with a topic or category (e.g., "poetry books") rather than a specific title or author, code as 'Finding relevant sources'.
7.	POSSESSION RULE: If a patron is "returning" or "bringing back" an item, they possess it. DO NOT code it as 'Lost Items'. "Overdue" is a status, not a loss.
8.	SPECIFIC TITLE: Only use a 'Known Item' code if a patron or user provides a specific title (e.g., "The Iliad"). Do NOT code as 'Known Item' if a librarian finds or suggests a specific title while helping to search or found from a topic.    Specific titles found during discovery are "results," not "intents."
9.	ACCESS vs. SEARCHING ISSUES: If user is struggling to get into an online resource (logins, "not allowed" messages, link errors), use 'Connectivity & Remote Access Issues' If user is inside using a database but doesn't know how to use it (limiters, Boolean operators, filters), use 'Database Search Skills'.
10.	RENEWALS/RETURNS: If the user is renewing or returning a technology-based item, use 'Renewals' first and 'Borrow Tech' second
11.	DO NOT INFER COURSE RESERVES: Do not assume a student needs 'Course Reserves' just because their request or need mentions a class or course.
12.	DO NOT INFER FORMATS: Example - Music Scores = 'Known Item: Other'. Never 'AV'
13.	FINANCIAL RULE: Use 'Fines & Fees' if billing/invoices/costs are mentioned.
14.	KNOWN ITEM CLARIFICATION:  Only use ‘Known Item’ for specific, named items. Asking for ‘2 articles’ or ‘5-6 books’ is ‘Finding Relevant Resources’

### FEW-SHOT TIE-BREAKERS
1.	Transcript: "Professor Jones here, need a laptop for my class." -> Code: Borrow Tech | Reasoning: Explicit request is for hardware. Excluded Faculty Support as no pedagogy help was requested.
2.	Transcript: "Need more licenses for REL 111 ebook." -> Code: Request Purchase | Reasoning: Explicit request for more access/licenses. Excluded Course Reserves as this is an acquisition issue.
3.	Transcript: "I need to renew my MacBook for another week."-> Code: Renewals, Borrow Tech | Reasoning: Mandatory Pairing applied. 'Renewals' for the action, 'Borrow Tech' for the item (laptop).
4.	Transcript: "My laptop is overdue, will the library be open at 7pm for me to return it?"-> Code: Borrow Tech, Hours | Reasoning: 'Borrow Tech' for the laptop. 'Hours' for the return time inquiry. (Note: NOT 'Lost Items' as the patron has the item).
5.	Transcript: "The A/C is broken on the 3rd floor." - Code: Other | Reasoning: Facility issue. No explicit request for 'Wayfinding' or mentions of 'Noise Issues' occurred.
6.	Transcript: "I need to find some poetry books for my English class." Code: Finding relevant sources | Reasoning: The patron is looking for a category/genre of material, not a specific known title.
7.	Transcript: "Do you have 'The Great Gatsby'?" Code: Known Item: Books | Reasoning: The patron provided a specific, unique title at the start.
8.	Transcript: "I'm researching New Orleans jazz. Can you help?" ... [later] ... Librarian: "Try the book 'Jazz Origins'." - Code: Finding relevant sources | Reasoning: Patron started with a topic. Librarian-suggested titles do not trigger 'Known Item' per Origin of Search Rule.
9.	Transcript: "The system says I still have this book, but I returned it. Billing sent me an invoice." - Code: Patron Accounts, Fines & Fees - Reasoning: 'Patron Accounts' for the system status check, 'Fines & Fees' for the billing mention. Do not code as Known Item: Books because the title was only given for account resolution. 
10.	Transcript: "Need the score for Beethoven's 5th." - Code: Known Item: Other | Reasoning: Music scores are a format not listed elsewhere. Excluded 'AV' per DO NOT INFER FORMATS rule.

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
