import pandas as pd
import time
import os
from coding_logic import call_gemini_api, master_prompt
from preprocessing_util import clean_and_normalize_transcript

# --- CONFIGURATION ---
INPUT_FILE = '/content/drive/MyDrive/Colab_Outputs/Master_Transcripts_34k.csv'
OUTPUT_FILE = '/content/drive/MyDrive/Colab_Outputs/Processed_Batch_1.csv'

# Set your batch parameters
BATCH_SIZE = 5000 
START_ROW = 0  # Change this for the next batch (e.g., 5000, 10000, etc.)

def run_batch_process():
    print(f"🚀 Starting Batch: Rows {START_ROW} to {START_ROW + BATCH_SIZE}")
    
    # 1. Load the specific slice of the CSV
    # Note: skiprows=range(1, START_ROW+1) keeps the header but skips previous data
    try:
        if START_ROW == 0:
            df = pd.read_csv(INPUT_FILE, nrows=BATCH_SIZE)
        else:
            # We skip the first N rows but keep the header (row 0)
            df = pd.read_csv(INPUT_FILE, skiprows=range(1, START_ROW + 1), nrows=BATCH_SIZE)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    # 2. Initialize a list to hold results (prevents total data loss if script stops)
    results = []

    # 3. Loop through the batch
    for index, row in df.iterrows():
        study_id = row['StudyID']
        transcript_text = row['Cleaned_Transcript'] # Ensure this column name matches your file
        
        try:
            # --- YOUR API CALL GOES HERE ---
            # response = call_gemini_api(transcript_text, master_prompt)
            # For now, we'll placeholder it:
            ai_output = "AI_Response_Placeholder" 
            
            # Append result
            results.append({
                'StudyID': study_id,
                'New_AI_Final_Code': ai_output,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Progress marker every 100 rows
            if (index + 1) % 100 == 0:
                print(f"✅ Processed {index + 1} / {BATCH_SIZE}...")

        except Exception as api_error:
            print(f"⚠️ Error on StudyID {study_id}: {api_error}")
            results.append({'StudyID': study_id, 'New_AI_Final_Code': "ERROR", 'Processed_At': None})

    # 4. Save results to a NEW file for this batch
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"🏁 Batch Complete! Output saved to: {OUTPUT_FILE}")

# Run the script
run_batch_process()
