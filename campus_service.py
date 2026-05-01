import pandas as pd
import time
import os
import re
from google.colab import userdata  # Assuming you are running this in Google Colab
from google.genai import Client

# Initialize the GenAI client
client = genai.Client(
    api_key=userdata.get('My_Key'),
    vertexai=False,
    http_options=types.HttpOptions(api_version='v1beta')
)

# --- 1. SETUP ---
MODEL_ID = "gemini-2.0-flash-lite"

INPUT_PATH = '/content/drive/MyDrive/34Batch/Combined/AZCombine/campus_AZ2.csv'
OUTPUT_PATH = '/content/drive/MyDrive/34Batch/Combined/AZCombine/services_AZ12.csv'

# --- 2. LOAD OR RESUME ---
if os.path.exists(OUTPUT_PATH):
    df = pd.read_csv(OUTPUT_PATH)
    # Check if the column exists to avoid errors on resume
    if 'AI_Qualitative_Analysis' not in df.columns:
        df['AI_Qualitative_Analysis'] = None
    print(f"✅ Resuming: {df['AI_Qualitative_Analysis'].notna().sum()} rows already completed.")
else:
    df = pd.read_csv(INPUT_PATH)
    df['AI_Qualitative_Analysis'] = None
    print("🚀 Starting fresh analysis.")

# --- 3. THE PRODUCTION LOOP ---
BATCH_SIZE = 5

for i in range(0, len(df), BATCH_SIZE):
    batch_indices = list(range(i, min(i + BATCH_SIZE, len(df))))
    batch = df.iloc[batch_indices]

    # Check if all rows in the current batch are already processed
    all_done = True
    for idx in batch_indices:
        if pd.isna(df.at[idx, 'AI_Qualitative_Analysis']) or str(df.at[idx, 'AI_Qualitative_Analysis']).strip() == "":
            all_done = False
            break
    
    if all_done:
        print(f"⏩ Batch {i} to {i + BATCH_SIZE - 1} already processed. Skipping...")
        continue

    print(f"Processing rows {i} to {min(i + BATCH_SIZE - 1, len(df) - 1)}...")

    # Build the transcript text block
    transcripts_text = ""
    for _, row in batch.iterrows():
        transcripts_text += f"ID: {row.get('StudyID')} | {row['OriginalTranscript']}\n"

    # The Prompt
    prompt = f"""
Role: You are a Senior Library Science Researcher specializing in qualitative analysis.
Tone & Voice: Maintain a supportive, insightful, and collaborative tone. Act as an intellectually rigorous peer who is invested in the success of this research project.
Task: Review the following chat transcripts that were previously coded as referencing a campus service or providing information about a campus service to the user.  Read the OriginalTranscript, AI_Thoughts and AI_Reasoning fields and identify and record the campus services the user was referred to.
Constraint:
• Do not summarize. Process every StudyID individually
• Exclude any reference or referral to a library service or resource

Output Format for each ID:
ID: [StudyID]
Services Referred: [Service]
Reasoning: [Reasoning in 2 brief sentences]

{transcripts_text}
"""
    
    try:
        # Generate content with 5-second delay
        time.sleep(5)
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        full_text = response.text

        # --- UNPACKING LOGIC: Row-by-Row Mapping ---
        # Search for each StudyID inside the returned text response
        for idx, row in batch.iterrows():
            study_id = str(row.get('StudyID'))
            
            # Use regex to find the block of text associated with this specific study_id
            pattern = rf"ID:\s*{study_id}(.*?)(?=ID:|\Z)"
            match = re.search(pattern, full_text, re.DOTALL)
            
            if match:
                # Capture the portion of the output belonging to the StudyID
                df.at[idx, 'AI_Qualitative_Analysis'] = match.group(1).strip()
            else:
                # If the AI response didn't match the standard text ID block pattern, save the full response text for manual review
                df.at[idx, 'AI_Qualitative_Analysis'] = f"No direct match found in response for {study_id}. Full Response:\n {full_text}"

        # --- FORCE SAVE TO DRIVE ---
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"💾 Checkpoint Saved for Batch {i}.")

    except Exception as e:
        print(f"⚠️ API Hiccup at row {i}: {e}. Waiting 30s...")
        time.sleep(30)

print("🏁 ANALYSIS COMPLETE.")
