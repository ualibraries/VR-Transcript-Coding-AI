import json
import os
import time
import pandas as pd
from google import genai
from google.colab import userdata
from preprocessing_util3 import clean_raw_text, AI_CONFIG, MODEL_NAME

# --- INITIALIZATION ---
client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

with open('codebook2.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

INPUT_FILE = "TestSet_Round10b.csv"
OUTPUT_FILE = "coded_resultsb.csv"
MAX_ROWS = 21
SAVE_INTERVAL = 5
TOTAL_EXPECTED = 20

# --- THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""

### NEGATIVE CONSTRAINTS (THE "NO-GO" ZONE)
•\tNO INVENTED CODES: Use ONLY the exact wording of the code keys as provided in the JSON Codebook (CODEBOOK_DICT).  Do not summarize or combine code names.  Each code must be its own distinct entry.
•\tNO INFERENTIAL CODING: Literal Evidence Only: You MUST only apply codes for intents explicitly stated by the patron or services performed by the librarian. DO NOT
•\tProhibited Language: In your reasoning, you are strictly forbidden from using words like "implies," "suggests," "could lead to," or "might mean".
•\tDO NOT INFER FORMATS: Example - Music Scores = 'Known Item: Other'. Never 'Known Item: AV’
•\tDO NOT INFER COURSE RESERVES: Do not assume a student needs 'Course Reserves' solely because their need mentions a class (ex. HUMS 150) or course (Applied Physics).
•\tDO NOT INFER ADDITIONAL IMPACTS: Do not infer secondary impacts (e.g., air conditioning issues do not automatically mean 'Noise Issues’, bad odors do not mean ‘Noise Issues’).

### CORE LOGIC.
•\tKeyword Contextualization: Map keywords to the "Intent" and "Definition" sections of the Codebook. Do not infer meaning not supported by a keyword.
•\tMulti-Labeling: Assign all relevant codes if a transcript touches multiple topics.  Separate with commas.  
•\tTopic/Genre: If patron starts with a topic, subject or category (e.g., "poetry books") rather than a known item, code as 'Finding relevant sources'.
•\tOrigin-Based Coding: A Known Item code (Book, Article, AV) can ONLY be triggered if the specific or unique item details (title, URL, etc.) originates from the Patron (including as a specific patron clarification e.g., "Yes, I'm looking for a book called X").
  •\tConfirmation Rule: If a patron merely acknowledges or "mentions" a title first introduced by the Librarian (e.g., "Yes, that's the Kansas City Star article I need"), it remains a result of Finding Relevant Resources, not a Known Item request.
•\tNoun-First Rule. Anchor first on the Object requested by the patron (the book, the report, the VR headset, the website). If a specific item is requested (the Noun), that is the Primary Intent. 
•\tLibrarian Source Rule: If it is the Librarian who suggests a specific resource (e.g., "Try the book 'Jazz Origins' or “Watch the film ‘Gone with the Wind’”)" this is a product of search and discovery, do NOT use 'Known Item'. 
•\tKnown Item Logical Immunity:
  •\tPurpose-Neutral: patron's goal for ‘known item’ request (e.g., literature review, lab report) does not change the known item request into a topic search.
  •\tAvailability-Neutral: Availability is not Intent. A search failure, referral to "Interlibrary Loan" or connectivity issue does not change the ‘Known Item’ intent. Do not change a ‘Known Item’ primary intent due to search or access failure or other secondary intents.
  •\tQuantity-Neutral: Multiple ‘Know Item’ requests (e.g. patron provided titles provided for three separate articles and a book) do not aggregate into a topic or subject search; the primary intent remains [Known Item: Format(s)] request.
•\tMetadate Density Rule: If the patron provides a unique identifier (title or URL or similiar) + Author, apply both [Known Item: Format] AND [Find Item by Author]. This captures the full metadata density of the request.
•\tRole-Based Anchor (Faculty Instructional Support)
  o\tExplicit Identity Required: Only apply Faculty Instructional Support if the user explicitly identifies as the teacher or instructor (e.g., "I am the professor," "for my students").
  o\tNo Inference from "Class": Do not assume a user is Faculty or Staff just because they mention a class (ex. HUMS 150) or course (Applied Physics) or uses "class," "assignment," or "research paper." Most students use these terms.
  o\tProfessional Capacity: Do NOT use Faculty Instructional Support if the user is staff/faculty but the request is for their own individual research or personal use (not for a course they are teaching).
•\tResearch Spectrum (Decision Tree)
  o\tDevelop Research Topic: Use if the Patron is still refining the idea or focus of their project.
  o\tResearch Strategies: Use if the Patron has a topic but needs a pathway (keywords, specific databases to try).
  o\tDatabase Search Skills: Use if the Librarian is teaching the mechanical use of a tool (how to use filters, Boolean operators, or interface features).
•\tPossession Rule: If a patron is "returning" or "bringing back" an item or claims it was already returned, it is NOT lost. DO NOT code it as 'Lost Items'.
•\tBuilding Maintenance: Inquiries regarding building comfort or maintenance such as HVAC (Air Conditioning/Heating), plumbing (leaks), lighting, or elevators are NOT related to Hours, Navigation & Wayfinding, or Noise Issues. You MUST use the code ‘Other’. 
•\tLibrary Web Navigation: Code as ‘Website’ if the interaction involves troubleshooting the Library Website interface (e.g., "click here," "scroll down," "I can't find it on the page"). This includes finding hours or info via the site's layout.
•\tPolicy: Any question regarding permission or rules for the library (e.g., "Am I allowed to...?", "Can I bring coffee?", “As an alumni, can I use...?”) MUST include the ‘Policies & Procedures’ code.
•\tAbandoned Chat: if there is zero evidence of a library-related inquiry with only items like greetings, thank you, nonsensical words or is blank, code as 'Abandoned Chat' If the librarian provides a link or discusses a policy, the chat is Active, even if the patron only says "Thank you". 
•\tTech Renewals: If the user is renewing or returning a technology-based item, use 'Renewals' first and 'Borrow Tech' second.  Do NOT use ‘Known Item’ for technology-based hardware.
•\tPhysical Wayfinding: If a permission or access question involves a specific library physical space (e.g., "Are the stacks open to community users?"), apply both ‘Policies & Procedures’ and ‘Navigation & Wayfinding’
•\tCampus Service Priority: If a librarian refers a patron to a non-library, university entity (Bookstore, Bursar, Financial Aid), the code ‘Campus Services’ is mandatory.

### FEW-SHOT EXAMPLES (THE ANCHORS)
Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Tech, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
Transcript: “I am a faculty member and I need a US Census dataset for my research paper” is Code: Known Item: Other | Reasoning: Patron is asking for known dataset for their own research project unrelated to teaching a class.
Transcript: "I want to donate 50 books on the Mayans." is Code: Other | Reasoning: 'Donations' is not a valid code; map to 'Other'.
Transcript: "My password is not working for the library link." Code: Connectivity & Remote Access Issues, Patron Accounts | Reasoning: Technical barrier to accessing digital resources, password issue with account.
Transcript: "I will just purchase the textbook myself." Code: Other | Reasoning: User is discussing buying the item themself. 'Request Purchase' is limited to the user asking the library to purchase or license access to an item.
Transcript: "Do you have the New York Times?" Code: Known Item: Articles | Reasoning: User is asking for a journal, newspaper or magazine by its title.

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
        # Ensure consistent return type even for early exit
        return "Abandoned Chat | Insufficient data for classification", ""

    coffee_reminder = "\n\n### PRECISION CHECK: Identify all distinct categories from the taxonomy."
    last_error = "Unknown Error"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}{coffee_reminder}",
                config=AI_CONFIG
            )
            # Remove the early return statement here
            # return response.text.replace("**", "").replace("\n", " ").strip()

            thoughts = []
            final_answer_parts = []

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought:
                    thoughts.append(part.text)
                elif part.text:
                    final_answer_parts.append(part.text)

            clean_code = " ".join(final_answer_parts).replace("**", "").replace("\n", " ").strip()
            mental_process = " ".join(thoughts).replace("\n", " ").strip()

            return clean_code, mental_process

        except Exception as e:
            last_error = str(e)
            if "503" in last_error:
                wait = (attempt + 1) * 10
                print(f"⚠️ Server Busy. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(5)
    # Ensure consistent return type for error case
    return f"ERROR | {last_error[:50]}", ""

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
    if 'AI_Thoughts' not in df.columns:
        df['AI_Thoughts'] = ""

    df['Applied_Code_Reasoning'] = df['Applied_Code_Reasoning'].astype(str) 
    df['AI_Thoughts'] = df['AI_Thoughts'].astype(str)
   
    processed_this_session = 0
    
    try:
        for i, row in df.iterrows():
            if pd.notnull(df.at[i, 'Applied_Code_Reasoning']) and df.at[i, 'Applied_Code_Reasoning'].strip() != "" and "ERROR" not in str(df.at[i, 'Applied_Code_Reasoning']):
                continue

            print(f"📝 [{i+1}/{len(df)}] Coding...")
            
            # Unpack the tuple returned by code_transcript
            clean_code, mental_process = code_transcript(row['Transcript'])
            
            # Now assign the variables
            df.at[i, 'Applied_Code_Reasoning'] = clean_code
            df.at[i, 'AI_Thoughts'] = mental_process
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
