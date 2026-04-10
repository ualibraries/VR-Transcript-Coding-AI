import pandas as pd
import time
import os
from coding_logic_34 import code_transcript, SYSTEM_PROMPT 
from preprocessing_util import clean_raw_text

# --- CONFIGURATION ---
INPUT_FILE = '/content/drive/MyDrive/34Batch/NewPrompt.csv'
OUTPUT_FILE = '/content/drive/MyDrive/34Batch/NewPrompt_Batch_1.csv'

# Set your batch parameters
BATCH_SIZE = 5000  # Set this to 7 for your final small test, then 5000
START_ROW = 0     
SAVE_INTERVAL = 100 # Saves every 100 rows

def run_batch_process():
    print(f"🚀 Starting Batch: Rows {START_ROW} to {START_ROW + BATCH_SIZE}")
    
    try:
        if START_ROW == 0:
            df = pd.read_csv(INPUT_FILE, nrows=BATCH_SIZE)
        else:
            df = pd.read_csv(INPUT_FILE, skiprows=range(1, START_ROW + 1), nrows=BATCH_SIZE)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    results = []

    # 3. Loop through the batch
    for index, row in df.iterrows():
        study_id = row['StudyID']
        # Double check if your CSV column is 'Transcript' or 'Cleaned_Transcript'
        transcript_text = row['Transcript']  
        
        try:
            # --- THE ACTUAL API CALL ---
            ai_output, thoughts = code_transcript(transcript_text)
            
            # Append result
            results.append({
                'StudyID': study_id,
                'Transcript': transcript_text, 
                'New_AI_Final_Code': ai_output,
                'AI_Thoughts': thoughts,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # --- THE CHECKPOINT SAVE ---
            if (index + 1) % SAVE_INTERVAL == 0:
                checkpoint_df = pd.DataFrame(results)
                checkpoint_df.to_csv(OUTPUT_FILE, index=False)
                print(f"💾 Checkpoint Saved at row {index + 1}. Total batch progress: {((index + 1)/BATCH_SIZE)*100:.1f}%")
            
            print(f"✅ Processed StudyID {study_id}...")
            time.sleep(1.5)

        except Exception as api_error:
            print(f"⚠️ Error on StudyID {study_id}: {api_error}")
            results.append({
                'StudyID': study_id, 
                'Transcript': transcript_text,
                'New_AI_Final_Code': "ERROR", 
                'AI_Thoughts': str(api_error),
                'Processed_At': None
            })

    # 4. Final Save
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"🏁 Batch Complete! Output saved to: {OUTPUT_FILE}")

# Run the script
run_batch_process()
