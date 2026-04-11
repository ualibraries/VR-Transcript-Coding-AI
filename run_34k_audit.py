import pandas as pd
import time
import os
import sys

# Define the folder name on your Drive where the modules are located
DRIVE_MODULES_FOLDER = '34Batch'
MODULES_FULL_PATH = os.path.join('/content/drive/MyDrive', DRIVE_MODULES_FOLDER)

# Add the module path to sys.path so Python can find coding_logic_34.py
sys.path.append(MODULES_FULL_PATH)

# Temporarily change the current working directory to where the module is located
# This allows coding_logic_34.py to find codebook2.json using a relative path during import
original_cwd = os.getcwd()
os.chdir(MODULES_FULL_PATH)

try:
    # IMPORTANT: Importing 'code_transcript' because that is the name inside your .py file
    from coding_logic_34 import code_transcript, SYSTEM_PROMPT
    from preprocessing_util import clean_raw_text
finally:
    # Always change back to the original working directory after import
    os.chdir(original_cwd)

# --- CONFIGURATION ---
INPUT_FILE = '/content/drive/MyDrive/34Batch/MasterList_Final.csv'

# Set your batch parameters
BATCH_SIZE = 1000 # Start small to test, then move to 500 or 1000
START_ROW = 5
SAVE_INTERVAL = 5 # Saves every X rows

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
        transcript_text = row['OriginalTranscript']

        try:
            # --- THE ACTUAL API CALL ---
            ai_output, thoughts = code_transcript(transcript_text)

            # Append result - NOW INCLUDING THE TRANSCRIPT
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text,  # <--- Added this line
                'New_AI_Final_Code': ai_output,
                'AI_Thoughts': thoughts,
                'Processed_At': time.strftime("%Y-%m-%d %H:%M:%S")
            })

            print(f"✅ Processed StudyID {study_id}...")
            time.sleep(1.5)

        except Exception as api_error:
            print(f"⚠️ Error on StudyID {study_id}: {api_error}")
            results.append({
                'StudyID': study_id,
                'OriginalTranscript': transcript_text, # Keep the transcript even on error
                'New_AI_Final_Code': "ERROR",
                'AI_Thoughts': str(api_error),
                'Processed_At': None
            })

    # 4. Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_FILE, index=False)

  # --- DYNAMIC OUTPUT FILE (The Overwrite Shield) ---
# This automatically creates a new name based on your start and batch size
OUTPUT_FILE = f'/content/drive/MyDrive/34Batch/Coded_Batch_{START_ROW}_to_{START_ROW + BATCH_SIZE}.csv'# Create a unique name for THIS specific run

# Run the script
run_batch_process()
