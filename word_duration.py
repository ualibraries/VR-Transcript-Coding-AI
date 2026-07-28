import pandas as pd
import numpy as np

def calculate_word_count(text):
    """Calculates word count for a given transcript string."""
    if pd.isna(text) or not str(text).strip():
        return 0
    return len(str(text).split())

def assign_duration_tertile(duration):
    """
    Duration tertile logic:
    - Short: <= 211.8 seconds
    - Medium: > 211.8 and <= 498 seconds
    - Long: > 498 seconds
    - Missing: NaN / NaT / None
    """
    if pd.isna(duration):
        return "Missing"
    try:
        dur = float(duration)
        if dur <= 211.8:
            return "Short"
        elif dur <= 498.0:
            return "Medium"
        else:
            return "Long"
    except (ValueError, TypeError):
        return "Missing"

def assign_word_tertile(word_count):
    """
    Word count tertile logic:
    - Short: <= 100 words
    - Medium: > 100 and <= 187 words
    - Long: > 187 words
    """
    if pd.isna(word_count):
        return "Short"

    wc = int(word_count)
    if wc <= 100:
        return "Short"
    elif wc <= 187:
        return "Medium"
    else:
        return "Long"

def map_complexity(row):
    """
    Maps (Duration_Tertile, Word_Tertile) combination to
    Designation (Simple, Moderate, Complex) and Numeric Score (1, 2, 3).
    """
    dur = row['Duration_Tertile']
    words = row['Word_Tertile']

    # --- COMPLEX CATEGORY (3) ---
    if (dur == "Long" and words == "Long") or \
       (dur == "Long" and words == "Medium") or \
       (dur == "Medium" and words == "Long") or \
       (dur == "Missing" and words == "Long"):
        return "Complex", 3

    # --- MODERATE CATEGORY (2) ---
    elif (dur == "Medium" and words == "Medium") or \
         (dur == "Short" and words == "Medium") or \
         (dur == "Short" and words == "Long") or \
         (dur == "Missing" and words == "Medium"):
        return "Moderate", 2

    # --- SIMPLE CATEGORY (1) ---
    elif (dur == "Short" and words == "Short") or \
         (dur == "Long" and words == "Short") or \
         (dur == "Medium" and words == "Short") or \
         (dur == "Missing" and words == "Short"):
        return "Simple", 1

    # Catch-all fallback if any unhandled edge case occurs
    else:
        return "Simple", 1

def process_transcripts(input_csv_path, output_csv_path):
    print(f"Loading data from {input_csv_path}...")
    df = pd.read_csv(input_csv_path)

    # 1. Calculate Word Count
    print("Calculating word counts...")
    df['Word_Count'] = df['Transcript'].apply(calculate_word_count)

    # 2. Assign Tertiles
    print("Assigning duration and word count tertiles...")
    df['Duration_Tertile'] = df['Duration'].apply(assign_duration_tertile)
    df['Word_Tertile'] = df['Word_Count'].apply(assign_word_tertile)

    # 3. Apply Decision Matrix for Complexity Mapping
    print("Mapping complexity designations and numeric codes...")
    complexity_results = df.apply(map_complexity, axis=1)

    # Split returned tuple into designated columns
    df['Complexity_Designation'] = [res[0] for res in complexity_results]
    df['Complexity_Score'] = [res[1] for res in complexity_results]

    # Save output
    df.to_csv(output_csv_path, index=False)
    print(f"Success! Processed {len(df)} records. Saved results to {output_csv_path}\n")

    # Display Breakdown Summary
    print("=== COMPLEXITY BREAKDOWN SUMMARY ===")
    summary = df['Complexity_Designation'].value_counts()
    for category, count in summary.items():
        pct = (count / len(df)) * 100
        print(f" - {category}: {count} ({pct:.2f}%)")

if __name__ == "__main__":
    # Update these paths to match your local file names
    INPUT_FILE = "UA_Master_Combined_Rev.csv"
    OUTPUT_FILE = "UA_Master_complexity.csv"

    # Run the pipeline
    process_transcripts(INPUT_FILE, OUTPUT_FILE)
