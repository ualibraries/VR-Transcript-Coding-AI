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
DRIVE_MODULES_FOLDER = 'TestJune'
MODULES_FULL_PATH = os.path.join('/content/drive/MyDrive', DRIVE_MODULES_FOLDER)
if MODULES_FULL_PATH not in sys.path:
    sys.path.insert(0, MODULES_FULL_PATH)

# --- CONFIGURATION ---
# Point this to your new 50-transcript subset
INPUT_FILE = '/content/drive/MyDrive/TestJune/JuneAtomic.csv'

BATCH_SIZE = 115   # Atomic runs can handle larger batches safely
START_ROW = 0
SAVE_INTERVAL = 5

OUTPUT_FILE = f'/content/drive/MyDrive/TestJune/Atomic_Audit_{START_ROW}_to_{START_ROW + BATCH_SIZE}.csv'

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
        except Exception as e: # Added missing except block
            print(f"❌ Error processing StudyID {study_id}: {e}")
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text,
                'New_AI_Final_Code': 'ERROR',
                'AI_Thoughts': str(e),
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
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
run_atomic_audit()
