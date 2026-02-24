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
1.	NO INVENTED CODES: Use ONLY the exact wording of the keys as provided in the JSON Codebook. If it’s not in the JSON Coding Schema, it doesn't exist.
2.	NO IMAGINED IMPACTS: Do not infer secondary impacts (e.g., air conditioning issues do not automatically mean 'Noise', bad odors do not mean ‘Noise’).
3.	DO NOT INFER COURSE RESERVES: Do not assume a student needs 'Course Reserves' just because their request or need mentions a class (ex. HUMS 150) or course (Applied Physics).
4.	DO NOT INFER FORMATS: Example - Music Scores = 'Known Item: Other'. Never 'AV'

### CORE LOGIC.
1.	Multi-Labeling: Assign all relevant codes if a transcript touches multiple topics. Separate with commas.
2.	Keyword Contextualization: Map keywords to the "Intent" and "Definition" sections of the Codebook. Do not infer meaning not supported by a keyword.
3.	Abandoned Chat: Contains only greetings, thank you, nonsensical words or is blank, code as 'Abandoned Chat'
4.	Known Item Triggers: Code as Known Item if the patron provides a unique identifier.  This can include:
  •	Proper Nouns: Branded platforms (Wiley, JCR), Organizations (MGMA), or cultural shorthand (Cosmo).
  •	Specific Titles: Books, book chapters, journals, journal articles, government reports, or unique archival/administrative docs (e.g., "Syllabus for PHYS 541, 2012").
  •	Metadata: URLs, ISBNs, or article citations.
5.	Logical Immunity:
  •	Purpose-Neutral: A patron's goal for a known item (e.g., "for a literature review") does not change a specific item request into a topic search.
  •	Inventory-Neutral: If the library doesn't own the item or the librarian suggests a referral (ILL/Bookstore), the intent remains Known Item. Never downgrade primary intent due to search failure.
  •	Library Availability: If a patron asks whether the library has a subscription or access to a specific title or resource (e.g., 'Does the library have a subscription to Harvard Business Review?'), the intent remains Known Item
  •	Multi-Part Requests: Multiple specific titles do not aggregate into a subject search; they remain a multi-part Known Item request.
6.	Platform Rule:  Requests for access to branded databases or research platforms (JCR, McGraw Hill Medicine, Scopus) code as ‘Known Item: Articles’ if they are primarily used to access periodical content, or ‘Known Item: Other’ if unknown
7.	Librarian Source Rule: If the Librarian suggests a specific title (e.g., "Try the book 'Jazz Origins'") as part of discovery, do NOT use 'Known Item'.
8.	Topic/Genre: If user start with a topic or category (e.g., "poetry books") rather than a specific title or author, code as 'Finding relevant sources'.
9.	Faculty Instructional Support: use 'Faculty Instructional Support' for class tours, pedagogy, instruction or curriculum design help. Do NOT code as 'Faculty Instructional Support' just because user identifies themselves as faculty.
10.	Possession Rule: If a patron is "returning" or "bringing back" an item or claims it was returned, it is NOT loss. DO NOT code it as 'Lost Items'.
11.	Tech Renewals: If the user is renewing or returning a technology-based item, use 'Renewals' first and 'Borrow Tech' second
12.	Building Maintenance: Inquiries regarding building comfort or maintenance such as HVAC (Air Conditioning/Heating), plumbing (leaks), lighting, or elevators are NOT related to Hours, Navigation & Wayfinding, or Noise Issues. You MUST use the code ‘Other’. 
13.	Library Web Navigation: Code as ‘Website’ if the interaction involves troubleshooting the Library Website interface (e.g., "click here," "scroll down," "I can't find it on the page"). This includes finding hours or info via the site's layout.
14.	Connectivity: Troubleshooting a broken link or authentication for a specific ‘Known Item’ resource is ‘Connectivity & Remote Access Issues’ and ‘Known Item’
15.	Policy vs. Info: Any question regarding permission or rules for the library (e.g., "Am I allowed to...?", "Can I bring coffee?") MUST be coded as ‘Policies & Procedures’.
16.	Physical Wayfinding: If a permission or access question involves a specific physical space (e.g., "Are the stacks open?"), apply both ‘Policies & Procedures’ and ‘Navigation & Wayfinding’
17.	Campus Service Priority: If a librarian refers a patron to a non-library entity (Bookstore, Bursar, Financial Aid), the code ‘Campus Service’ is mandatory.
18. Compound Intent Rule: If the patron provides a Title + Author, apply [Known Item: Format] AND [Find Item by Author]. This captures the full metadata density of the request.

### FEW-SHOT EXAMPLES (THE ANCHORS)
•	Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Tech, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
•	Transcript: "I want to donate 50 books on the Mayans." is Code: Other | Reasoning: 'Donations' is not a valid code; map to 'Other'.
•	Transcript: "My password is not working for the library link." Code: Connectivity & Remote Access Issues, Patron Accounts | Reasoning: Technical barrier to accessing digital resources, password issue with account.
•	Transcript: "I will just purchase the textbook myself." Code: Other | Reasoning: User is discussing buying the item themself. 'Request Purchase' is limited to the library purchasing an item or access to an item.
•	Transcript: "Do you have the New York Times?" Code: Find a Known Item: Journals, Periodicals, or Articles | Reasoning: User is asking for a journal, newspaper or magazine by its title.

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
