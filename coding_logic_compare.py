import json
import os
import time
import pandas as pd
from google import genai
from google.colab import userdata
# We only import the specific items defined in your utils file
from preprocessing_modelcompare import clean_raw_text, AI_CONFIG, MODEL_NAME, OUTPUT_FILE

# --- INITIALIZATION ---
client = genai.Client(api_key=userdata.get('GEMINI_API_KEY'))

with open('codebook.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

INPUT_FILE = "ModelTest5.csv"
SAVE_INTERVAL = 10

SYSTEM_PROMPT = f"### 



CODEBOOK JSON:\n{json.dumps(CODEBOOK_DICT, indent=2)}"

def code_transcript(transcript):
    cleaned_input = clean_raw_text(transcript)
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data", ""

    coffee_reminder = "\n\n### PRECISION CHECK: Use 'Other' if no fit. No definitions 'stretching'."
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}{coffee_reminder}",
                config=AI_CONFIG 
            )
            
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
            time.sleep(5)
    
    return "ERROR | Response failed", ""

def main():
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE)
    else:
        df = pd.read_csv(INPUT_FILE)

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

            print(f"📝 Coding row {i+1} with {MODEL_NAME}...")
            clean_code, mental_process = code_transcript(row['Transcript'])
            
            df.at[i, 'Applied_Code_Reasoning'] = clean_code
            df.at[i, 'AI_Thoughts'] = mental_process
            processed_this_session += 1

            if processed_this_session % SAVE_INTERVAL == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                print(f"💾 Saved {OUTPUT_FILE}")
                      
            time.sleep(1.0) 

    except KeyboardInterrupt:
        print("\n🛑 Manual stop.")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"🏁 Final Save Complete. Session Total: {processed_this_session}")

if __name__ == "__main__":
    main()
