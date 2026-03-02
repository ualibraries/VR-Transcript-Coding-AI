def code_transcript(transcript):
    """
    Orchestrates the API call with retries and the 'AI Coffee' freshness injection.
    """
    cleaned_input = clean_raw_text(transcript)
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data for classification"
# Updated Coffee Reminder

    coffee_reminder = "\n\n### PRECISION CHECK: Identify all distinct categories from the taxonomy."
    last_error = "Unknown Error"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}{coffee_reminder}",
                config=AI_CONFIG 
            )
            return response.text.replace("**", "").replace("\n", " ").strip()

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
            last_error = str(e)
            if "503" in last_error:
                wait = (attempt + 1) * 10
                print(f"⚠️ Server Busy. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(5)

    return f"ERROR | {last_error[:50]}"

def main():
    # 1. Load the Data
    if os.path.exists(OUTPUT_FILE):
        print(f"📂 Found existing progress. Resuming from {OUTPUT_FILE}...")
        df = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"🆕 Starting fresh with {INPUT_FILE}...")
        df = pd.read_csv(INPUT_FILE)

    # FIX: Explicitly ensure the column exists and is treated as a String/Object
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

            print(f"📝 [{i+1}/{len(df)}] Coding...")
            df.at[i, 'Applied_Code_Reasoning'] = code_transcript(row['Transcript'])
            processed_this_session += 1

            df.at[i, 'Applied_Code_Reasoning'] = clean_code
            df.at[i, 'AI_Thoughts'] = mental_process
            processed_this_session += 1

            if processed_this_session % SAVE_INTERVAL == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                progress = (i / TOTAL_EXPECTED) * 100
                print(f"💾 Saved Checkpoint. Total Progress: {progress:.1f}%")
            time.sleep(2.0) # Reduced sleep; Flash can handle higher RPS
                      
    except KeyboardInterrupt:
        print("\n🛑 Manual stop. Saving...")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"🏁 Final Save Complete. Session Total: {processed_this_session}")

if __name__ == "__main__":
    main()
