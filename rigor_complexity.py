import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. DEFINE RIGOR TIER DICTIONARY (Tier 1 to Tier 6)
# ---------------------------------------------------------
CODE_RIGOR_TIERS = {
    # Tier 1 (Weight 1) - Directional / Operational
    'Campus Services': 1, 'Campus Wayfinding': 1, 'Hours': 1,
    'Lost & Found': 1, 'Navigation & Wayfinding': 1, 'Noise Issues': 1,
    'Physical Accessibility': 1, 'Study Rooms & Reservations': 1,

    # Tier 2 (Weight 2) - Access & Basic Account Rules
    'Fines & Fees': 2, 'Hold Request': 2, 'Lost Items': 2,
    'Patron Account': 2, 'Renewals': 2, 'Policies & Procedures': 2,

    # Tier 3 (Weight 3) - Technical & Access Support
    'Borrow Tech': 3, 'Connectivity & Remote Access Issues': 3,
    'Software': 3, 'Tech Support': 3, 'Website': 3, 'Printing & Scanning': 3,

    # Tier 4 (Weight 4) - Specialized Library Workflows
    'Course Reserves': 4, 'Faculty Instructional Support': 4,
    'Interlibrary Loan': 4, 'Library Services': 4, 'Request Purchase': 4,

    # Tier 5 (Weight 5) - Known Item & Bibliographic Identification
    'Find by Author': 5, 'Known Item: Article': 5, 'Known Item: AV': 5,
    'Known Item: Book': 5, 'Known Item: Other': 5, 'Known Item: Thesis': 5,

    # Tier 6 (Weight 6) - In-Depth Research & Pedagogy (READ Scale 4-6)
    'Citations / Citing Sources': 6, 'Database Search Skills': 6,
    'Develop Research Topic': 6, 'Evaluating Information': 6,
    'Finding Relevant Resources': 6, 'Managing & Organizing Information': 6,
    'Research': 6
}

def calculate_max_rigor(codes_entry):
    """
    Parses assigned codes from 'AI_Final_Code' and returns the highest Tier weight (R_max).
    Handles string lists, bracketed arrays, and comma-separated text.
    """
    if pd.isna(codes_entry) or not str(codes_entry).strip():
        return 1  # Default fallback to Tier 1 if no code is present

    # Clean up formatting artifact characters like brackets or extra quotes
    cleaned_str = str(codes_entry).replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    codes_list = [c.strip() for c in cleaned_str.split(',') if c.strip()]

    # Identify maximum tier present
    max_tier = 1
    for code in codes_list:
        tier = CODE_RIGOR_TIERS.get(code, 1)
        if tier > max_tier:
            max_tier = tier

    return max_tier

def compute_composite_complexity(df, target_code_col='AI_Final_Code', w_v=0.20, w_d=0.30, w_r=0.50):
    """
    Reads 'AI_Final_Code', calculates R_max, normalizes components,
    and outputs Composite Complexity Index (C_s).
    """
    if target_code_col not in df.columns:
        raise KeyError(f"Specified column '{target_code_col}' not found in DataFrame.")

    # 1. Calculate Max Rigor Rank (R_max) from AI_Final_Code
    print(f"Calculating Max Rigor Rank (R_max) using column '{target_code_col}'...")
    df['R_max'] = df[target_code_col].apply(calculate_max_rigor)

    # 2. Normalize Volume Component (V_norm: Complexity_Score 1-3 -> 0.0-1.0)
    V_norm = (df['Complexity_Score'] - 1) / (3 - 1)

    # 3. Normalize Intent Density Component (D_norm: Intent_Count 1-10 -> 0.0-1.0)
    # Cap at 10 to protect against extreme outliers
    D_norm = np.clip((df['Intent_Count'] - 1) / (10 - 1), 0.0, 1.0)

    # 4. Normalize Rigor Component (R_norm: R_max 1-6 -> 0.0-1.0)
    R_norm = (df['R_max'] - 1) / (6 - 1)

    # 5. Calculate Final Composite Score (C_s) scaled 0-100
    print("Calculating Composite Complexity Score (C_s)...")
    df['Composite_Complexity_Score'] = 100 * (
        (V_norm * w_v) +
        (D_norm * w_d) +
        (R_norm * w_r)
    )

    df['Composite_Complexity_Score'] = df['Composite_Complexity_Score'].round(2)

    return df

# ---------------------------------------------------------
# EXECUTION PIPELINE
# ---------------------------------------------------------
if __name__ == "__main__":
    input_file = "UA_Master_complexity.csv"
    output_file = "UA_Master_composite_complexity_rev.csv"

    df = pd.read_csv(input_file)

    # Automatically derive Intent_Count from AI_Final_Code if not already populated
    if 'Intent_Count' not in df.columns or df['Intent_Count'].isnull().all():
        print("Deriving 'Intent_Count' directly from 'AI_Final_Code'...")
        df['Intent_Count'] = df['AI_Final_Code'].apply(
            lambda x: len([c for c in str(x).replace("[", "").replace("]", "").replace("'", "").replace('"', '').split(',') if c.strip()])
            if pd.notna(x) else 1
        )

    # Compute final metrics targeting AI_Final_Code
    df_result = compute_composite_complexity(df, target_code_col='AI_Final_Code')

    df_result.to_csv(output_file, index=False)
    print(f"\nSuccess! Processed {len(df_result)} rows using 'AI_Final_Code'. Results saved to '{output_file}'.")
