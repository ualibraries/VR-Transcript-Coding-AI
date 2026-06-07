import json
import os
import time
import pandas as pd
from google import genai
from google.genai import types
from google.colab import userdata
from preprocessing_util import clean_raw_text, AI_CONFIG, MODEL_NAME

# --- INITIALIZATION ---
client = genai.Client(
    api_key=userdata.get('GEMINI_API_KEY'),
    vertexai=False,
    http_options=types.HttpOptions(api_version='v1beta')
)

with open('codebook_cluster.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

# 2. Define the Rigid Codebook Guidelines (System Prompt)
SYSTEM_PROMPT = f"""
You are a Quality Assurance assistant. Your job is to prevent overcoding, hallucinations and other misinterpretations of the codebook from the codebook_cluster.json file.
Review and compare the codes assigned by the original Gemini AI coder and ensure that only codes with direct, strong conceptual alignment are included.
"""

def audit_record(row):
    """Processes a single row and requests flat, pipe-separated values from Gemini."""
    
    # Helper to clean up pandas NaN or missing values on the fly
    def clean_val(val):
        return 'N/A' if pd.isna(val) or str(val).strip() == '' else str(val)

    # Consolidate the row information cleanly for the model context
    user_content = f"""
    --- RECORD TO AUDIT ---
    StudyID: {clean_val(row.get('StudyID'))}
    Institution: {clean_val(row.get('Institution'))}
    Transcript: {clean_val(row.get('Transcript'))}
    Current Codes Assigned: {clean_val(row.get('New_AI_Final_Code'))}
    Applied Code Reasoning: {clean_val(row.get('New_AI_Reasoning'))}
    AI Thoughts: {clean_val(row.get('AI_Thoughts'))}
    -----------------------
    Perform your audit balancing the guidelines. 
    Output exactly ONE line of text containing these 5 fields separated strictly by a pipe character (|).
    
    Fields to output:
    Applied Code | Reasoning For Applied Code | Recommended Code Changes | Reason For Code Changes | Final Resolved Code
    
    *NOTE for 'Final Resolved Code': If there are no changes, output the exact 'Current Codes Assigned'. If you recommended changes, output what the complete, clean final list of codes should look like after applying your recommendations.*
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,  # Kept low for strict codebook compliance
            ),
        )
        
        # Split the pipe-delimited text response into a list of strings
        fields = [f.strip() for f in response.text.split('|')]
        
        # Guard: Ensure we always return exactly 4 fields to prevent column misalignment
        if len(fields) < 5:
            fields.extend(["N/A"] * (5 - len(fields)))
        return fields[:5]
        
    except Exception as e:
        print(f"Error processing StudyID {row.get('StudyID')}: {e}")
        # Fallback fields matching the format to preserve the CSV row layout
        return ["API Error", "API Error Interruption", "ERROR", str(e), "ERROR"]


def run_batch_audit(input_csv_path, output_csv_path, max_rows=None, save_interval=None, start_row=0):
    """Reads input CSV, handles slicing offsets, and outputs a flat CSV report."""
    df = pd.read_csv(input_csv_path)
    
    # Apply starting row offset if picking up from a partial run
    if start_row > 0:
        print(f"Skipping the first {start_row} rows...")
        df = df.iloc[start_row:].reset_index(drop=True)
        
    if max_rows:
        df = df.head(max_rows)

    audit_results = []
    total_records = len(df)
    print(f"Starting audit loop for {total_records} records...")

    # Modular internal helper to save progress dynamically without data corruption
    def save_progress_to_csv(results, path):
        if not results:
            return
        temp_df = pd.DataFrame(results, columns=[
            '[StudyID]', 
            '[Applied Code]', 
            '[Reasoning for Applied Code]', 
            '[Recommended Code Changes]', 
            '[Reason for Code Changes]',
            '[Final Code]'
        ])
        temp_df.to_csv(path, index=False)

    try:
        for idx, row in df.iterrows():
            print(f"Auditing index {idx + 1}/{total_records} (StudyID: {row.get('StudyID')})")

            # Get the flat 4-field list from the model
            ai_output = audit_record(row)
            
            # Combine the row's StudyID with the 4 fields from the model
            row_result = [str(row.get('StudyID', 'N/A'))] + ai_output
            audit_results.append(row_result)

            # Checkpoint Save logic
            if save_interval and (idx + 1) % save_interval == 0:
                save_progress_to_csv(audit_results, output_csv_path)
                progress = ((idx + 1) / total_records) * 100
                print(f"💾 Checkpoint Saved. Total Progress: {progress:.1f}%")

            # Active wait to respect API rate limits
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n🛑 Manual stop detected during processing. Saving current progress...")
        if audit_results:
            save_progress_to_csv(audit_results, output_csv_path)
            print(f"Partial audit results saved to: {output_csv_path}")
        raise 

    # Final save after loop completes successfully
    if audit_results:
        save_progress_to_csv(audit_results, output_csv_path)
        print(f"Audit completed successfully! Saved to: {output_csv_path}")
    else:
        print("No records processed or saved.")


# --- Execution Entry Point ---
if __name__ == "__main__":
    INPUT_FILE = '/content/drive/MyDrive/TestJune/Adjudicated1746_June.csv'
    OUTPUT_FILE = '/content/drive/MyDrive/TestJune/Verified1746_June.csv'
    
    START_ROW = 0      # Set to skip rows (e.g., set to 500 to pick up after the 500th row)
    SAVE_INTERVAL = 5  # Saves your spreadsheet every 5 records
    MAX_ROWS = 20      # Set to None to run the complete file

    try:
        run_batch_audit(
            input_csv_path=INPUT_FILE, 
            output_csv_path=OUTPUT_FILE, 
            max_rows=MAX_ROWS, 
            save_interval=SAVE_INTERVAL,
            start_row=START_ROW
        )
    except Exception as e:
        print(f"An error occurred during batch audit: {e}")
