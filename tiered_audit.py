import pandas as pd
import numpy as np

def consensus_audit_workflow(input_file, output_file):
    print(f"📂 Processing {input_file}...")
    df = pd.read_csv(input_file)

    # --- STEP 1: PRE-AUDIT CLEANUP (Splitting Logic) ---
    # We check if the columns already exist; if not, we split the raw column
    if 'Applied_Code_Reasoning' in df.columns and 'New_AI_Final_Code' not in df.columns:
        print("✂️ Splitting 'Applied_Code_Reasoning' into Code and Reasoning...")
        split_data = df['Applied_Code_Reasoning'].str.split('|', n=1, expand=True)
        df['New_AI_Final_Code'] = split_data[0].str.strip()
        df['New_AI_Reasoning'] = split_data[1].str.strip() if len(split_data.columns) > 1 else ""

    # --- STEP 2: NORMALIZATION (Ensures 'Hours' matches 'Hours ') ---
    def clean_codes(val):
        if pd.isna(val) or str(val).strip().lower() == 'nan' or not str(val).strip():
            return set()
        # Clean specific artifacts and standardize case
        return {c.strip().lower().rstrip('s') for c in str(val).split(',')}

    # --- STEP 3: TIERED CLASSIFICATION ---
    def classify_tier(row):
        # Extract Human Codes (Codes 1, 2, 3)
        h_cols = ['Code 1', 'Code 2', 'Code 3']
        human = set()
        for col in h_cols:
            if col in row and pd.notna(row[col]):
                human.update(clean_codes(row[col]))
        
        # Extract AI Codes
        ai = clean_codes(row.get('New_AI_Final_Code', ''))
        
        if not human and not ai: return 'Match (Both Empty)'
        if human == ai: return 'Match'
        
        intersection = human.intersection(ai)
        
        # Tier 1: Total Mismatch (Zero overlap)
        if not intersection and human and ai:
            return 'Tier 1: Total Mismatch'
        
        # Tier 2: Intent Expansion (AI found everything human did + MORE)
        if human.issubset(ai):
            return 'Tier 2: AI Intent Expansion'
        
        # Tier 3: Intent Contraction (Human found things AI missed)
        if ai.issubset(human):
            return 'Tier 3: AI Intent Contraction'
            
        # Complex Overlap (Mixed additions and misses)
        return 'Tier 4: Complex Overlap'

    df['Audit_Tier'] = df.apply(classify_tier, axis=1)

    # --- STEP 4: GENERATE AUDIT DIFF NOTES ---
    def generate_diff(row):
        h_cols = ['Code 1', 'Code 2', 'Code 3']
        human = set()
        for col in h_cols:
            if col in row and pd.notna(row[col]): human.update(clean_codes(row[col]))
        ai = clean_codes(row.get('New_AI_Final_Code', ''))
        
        added = ai - human
        missed = human - ai
        
        notes = []
        if added: notes.append(f"AI ADDED: {', '.join(added)}")
        if missed: notes.append(f"AI MISSED: {', '.join(missed)}")
        return " | ".join(notes) if notes else "No Change"

    df['Audit_Diff_Notes'] = df.apply(generate_diff, axis=1)

    # --- STEP 5: SORT AND SAVE ---
    tier_order = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap', 
                  'Tier 3: AI Intent Contraction', 'Tier 2: AI Intent Expansion', 'Match']
    df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)
    df = df.sort_values('Audit_Tier')

    df.to_csv(output_file, index=False)
    
    # Report the new breakdown
    print("\n" + "="*30)
    print("CONSENSUS AUDIT REPORT")
    print("="*30)
    print(df['Audit_Tier'].value_counts().sort_index())
    print("="*30)
    print(f"Done! Open '{output_file}' to begin Expert Adjudication.")

# Run it
if __name__ == "__main__":
    consensus_audit_workflow('CodedResults1747.csv', 'Adjudication_Master_List.csv')
