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
# We add verify_coding to our imports (we will create this script next)
from coding_logic_34 import code_transcript
from verifier_logic import verify_coding  
from preprocessing_util import clean_raw_text

# --- CONFIGURATION ---
INPUT_FILE = '/content/drive/MyDrive/34Batch/MasterList_Final.csv'
BATCH_SIZE = 50  # We can set this higher now because each call is atomic
START_ROW = 0    
SAVE_INTERVAL = 5 

OUTPUT_FILE = f'/content/drive/MyDrive/34Batch/Atomic_Coded_{START_ROW}_to_{START_ROW + BATCH_SIZE}.csv'

def run_atomic_multi_agent_process():
    print(f"🚀 Starting Atomic Multi-Agent Process: Rows {START_ROW} to {START_ROW + BATCH_SIZE}")
    
    # Load slice
    try:
        df = pd.read_csv(INPUT_FILE, skiprows=range(1, START_ROW + 1), nrows=BATCH_SIZE)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    results = []

    for index, row in df.iterrows():
        study_id = row['StudyID']
        transcript_text = row['OriginalTranscript']
        
        # ATOMIC STEP 1: INITIAL CODING
        try:
            # We call the coder
            ai_output, thoughts = code_transcript(transcript_text)
            
            # ATOMIC STEP 2: VERIFICATION (The "Glass Box" Audit)
            # We pass the transcript AND the coder's output to the Verifier
            is_valid, feedback = verify_coding(transcript_text, ai_output)
            
            # ATOMIC STEP 3: RE-CODING (If Verifier finds a logic error)
            if not is_valid:
                print(f"⚠️ Verifier flagged StudyID {study_id}. Retrying with feedback...")
                # We send the feedback back to the coder for a one-time correction
                ai_output, thoughts = code_transcript(transcript_text, feedback=feedback)
            
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text, 
                'Final_Code': ai_output,
                'Audit_Feedback': feedback if not is_valid else "PASS",
                'AI_Thoughts': thoughts,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"✅ Verified & Saved StudyID {study_id}")

        except Exception as e:
            print(f"⚠️ Critical Failure on {study_id}: {e}")
            results.append({'StudyID': study_id, 'Final_Code': "ERROR", 'AI_Thoughts': str(e)})

        # Save checkpoint
        if (index + 1) % SAVE_INTERVAL == 0:
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
            print(f"💾 Checkpoint: {index + 1} rows.")

        time.sleep(2) # Keeping it polite for the API

    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"🏁 Process Complete. Results: {OUTPUT_FILE}")

run_atomic_multi_agent_process()
