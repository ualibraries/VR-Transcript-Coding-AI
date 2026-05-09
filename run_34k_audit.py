import pandas as pd
import time
import os
import sys
import importlib
from google.colab import drive

# 1. Mount Drive
if not os.path.exists('/content/drive'):
    drive.mount('/content/drive')

# 2. Setup Pathing
DRIVE_MODULES_FOLDER = '34Batch'
MODULES_FULL_PATH = os.path.join('/content/drive/MyDrive', DRIVE_MODULES_FOLDER)
if MODULES_FULL_PATH not in sys.path:
    sys.path.insert(0, MODULES_FULL_PATH)

# --- THE RESET SWITCH ---
# This forces the script to see the changes you made to the All-in-One file
import coding_logic_34
importlib.reload(coding_logic_34)
from coding_logic_34 import code_transcript_with_verify

# --- CONFIGURATION ---
# Point this to your new 50-transcript subset
INPUT_FILE = '/content/drive/MyDrive/34Batch/atomic_subset.csv' 

BATCH_SIZE = 50   # Atomic runs can handle larger batches safely
START_ROW = 0     
SAVE_INTERVAL = 5

OUTPUT_FILE = f'/content/drive/MyDrive/34Batch/Atomic_Audit_{START_ROW}_to_{START_ROW + BATCH_SIZE}.csv'

def run_atomic_audit():
    print(f"🚀 Starting All-in-One Atomic Audit: Rows {START_ROW} to {START_ROW + BATCH_SIZE}")
    print(f"📁 Saving to: {OUTPUT_FILE}")
    
    # 1. Load the slice
    try:
        df = pd.read_csv(INPUT_FILE, skiprows=range(1, START_ROW + 1), nrows=BATCH_SIZE)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    results = []

    # 2. Loop through transcripts
    for index, row in df.iterrows():
        study_id = row['StudyID']
        transcript_text = row['OriginalTranscript'] 
        
        try:
            # CALLING THE CONSOLIDATED BRAIN
            # This handles Initial Coding -> Verification -> Optional Revision
            final_code, audit_note, thoughts = code_transcript_with_verify(transcript_text)
            
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text, 
                'Final_Code': final_code,
                'Audit_Note': audit_note, # Tells you if it passed first try or was revised
                'AI_Thoughts': thoughts,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            status_icon = "✅" if audit_note == "PASS" else "⚠️"
            print(f"{status_icon} Processed {study_id} (Audit: {audit_note[:30]}...)")

        except Exception as e:
            print(f"❌ Critical Failure on {study_id}: {e}")
            results.append({
                'StudyID': study_id, 
                'Final_Code': "ERROR", 
                'Audit_Note': str(e),
                'AI_Thoughts': "Check API/Script Logic"
            })

        # --- THE CHECKPOINT SAVE ---
        if (index + 1) % SAVE_INTERVAL == 0:
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
            print(f"💾 Checkpoint saved at row {index + 1}")

        time.sleep(2) # Keeping the API happy

    # 3. Final Save
    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"🏁 Audit Complete! {len(results)} rows saved.")

# 4. RUN
run_atomic_audit()
