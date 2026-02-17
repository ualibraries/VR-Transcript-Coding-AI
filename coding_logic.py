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
Analyze the provided library chat transcripts strictly using the definitions in the following JSON Coding Schema. Your expertise is in applying codes from the official JSON Codebook with 100% precision.

### NEGATIVE CONSTRAINTS (THE "NO-GO" ZONE)
•	NO INVENTED CODES: Use ONLY the exact wording of the keys as provided in the JSON Codebook. If it’s not in the JSON Coding Schema, it doesn't exist.
•	NO IMAGINED IMPACTS: Do not infer secondary impacts (e.g., air conditioning issues do not automatically mean 'Noise', bad odors do not mean ‘Noise’).
•	DO NOT INFER COURSE RESERVES: Do not assume a student needs 'Course Reserves' just because their request or need mentions a class (ex. HUMS 150) or course (Applied Physics).
•	DO NOT INFER FORMATS: Example - Music Scores = 'Known Item: Other'. Never 'AV'
•	Building Maintenance: Inquiries regarding HVAC (Air Conditioning/Heating), plumbing (leaks), lighting, or elevators are NOT related to Hours, Navigation & Wayfinding, or Noise Issues.

### CORE LOGIC.
1.	Multi-Labeling: Assign all relevant codes if a transcript touches multiple topics. Separate with commas.
2.	Keyword Contextualization: Map keywords to the "Intent" and "Definition" sections of the Codebook. Do not infer meaning not supported by a keyword.
3.	THE LIBRARIAN SOURCE RULE: If the Librarian suggests a specific title (e.g., "Try the book 'Jazz Origins'") as part of discovery, do NOT use 'Known Item'.
4.	PATRON REQUEST RULE: Only the Patron providing a title triggers 'Known Item' or patron providing author triggers ‘Find by Author.’ Specific titles found during discovery are "results," not user "intents."
5.	TOPIC/GENRE: If user start with a topic or category (e.g., "poetry books") rather than a specific title or author, code as 'Finding relevant sources'.
6.	NO FACULTY OVER-CODING: Only use 'Faculty Instructional Support' for pedagogy, instruction or curriculum design help. If a patron says "I'm a faculty member looking for a book by…," the code is 'Find by Author', NOT 'Faculty Instructional Support'.
7.	POSSESSION RULE: If a patron is "returning" or "bringing back" an item, it is NOT loss. DO NOT code it as 'Lost Items'.
8.	TECH RENEWALS: If the user is renewing or returning a technology-based item, use 'Renewals' first and 'Borrow Tech' second
9.	KNOWN ITEM CLARIFICATION:  Only use ‘Known Item’ for specific, named items. Asking for ‘2 articles’ or ‘5-6 books’ is ‘Finding Relevant Resources’ NOT a ‘Know Item’ code.
10. The "Other" Mandate: If a patron’s primary intent is building comfort or maintenance, you MUST use the code Other. Do not "stretch" definitions of operational hours or physical locations to accommodate facility issues.

### FEW-SHOT EXAMPLES (THE ANCHORS)
Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Tech, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
Transcript: "I want to donate 50 books on the Mayans." is Code: Other | Reasoning: 'Donations' is not a valid code; map to 'Other'.
Transcript: "My password is not working for the library link." Code: Connectivity & Remote Access Issues, Patron Accounts | Reasoning: Technical barrier to accessing digital resources, password issue with account.

### RESPONSE FORMAT
Code, Code | [Reasoning: Brief justification for inclusion/exclusion]

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
