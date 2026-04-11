import pandas as pd
import time
import os
import sys
from google.colab import drive

# 1. Mount Drive
drive.mount('/content/drive')

# 2. Setup Pathing
DRIVE_MODULES_FOLDER = '34Batch'
MODULES_FULL_PATH = os.path.join('/content/drive/MyDrive', DRIVE_MODULES_FOLDER)
if MODULES_FULL_PATH not in sys.path:
    sys.path.append(MODULES_FULL_PATH)

# 3. Import Custom Functions
from coding_logic_34 import code_transcript, SYSTEM_PROMPT
from preprocessing_util import clean_raw_text

# --- CONFIGURATION ---
INPUT_FILE = '/content/drive/MyDrive/34Batch/MasterList_Final.csv'

# Set your batch parameters
BATCH_SIZE = 10
START_ROW = 10    
SAVE_INTERVAL = 5

# --- DYNAMIC OUTPUT FILE (The Overwrite Shield) ---
# This creates a unique filename like: Coded_Batch_0_to_1000.csv
OUTPUT_FILE = f'/content/drive/MyDrive/34Batch/Coded_Batch_{START_ROW}_to_{START_ROW + BATCH_SIZE}.csv'

def run_batch_process():
    print(f"🚀 Starting Batch: Rows {START_ROW} to {START_ROW + BATCH_SIZE}")
    print(f"📁 Output will be saved to: {OUTPUT_FILE}")
    
    # 1. Load the specific slice
    try:
        if START_ROW == 0:
            df = pd.read_csv(INPUT_FILE, nrows=BATCH_SIZE)
        else:
            df = pd.read_csv(INPUT_FILE, skiprows=range(1, START_ROW + 1), nrows=BATCH_SIZE)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    results = []

    # 2. Loop through the batch
    for index, row in df.iterrows():
        study_id = row['StudyID']
        transcript_text = row['OriginalTranscript'] 
        
        try:
            # The API Call
            ai_output, thoughts = code_transcript(transcript_text)
            
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text, 
                'New_AI_Final_Code': ai_output,
                'AI_Thoughts': thoughts,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            print(f"✅ Processed StudyID {study_id}...")

        except Exception as api_error:
            print(f"⚠️ Error on StudyID {study_id}: {api_error}")
            results.append({
                'StudyID': study_id, 
                'OriginalTranscript': transcript_text,
                'New_AI_Final_Code': "ERROR", 
                'AI_Thoughts': str(api_error),
                'Processed_At': None
            })

        # --- THE CHECKPOINT SAVE (FIXED) ---
        # Runs every 50 rows. ALIGNED with the 'try' block.
        if (index + 1) % SAVE_INTERVAL == 0:
            checkpoint_df = pd.DataFrame(results)
            checkpoint_df.to_csv(OUTPUT_FILE, index=False)
            print(f"💾 CHECKPOINT SAVED at row {index + 1}!")

        # The Politeness Breather
        time.sleep(1.5)

    # 3. Final Save
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"🏁 Batch Complete! {len(results)} rows saved to: {OUTPUT_FILE}")

# 4. RUN
run_batch_process()
