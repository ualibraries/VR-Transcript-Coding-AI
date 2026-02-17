import pandas as pd
import numpy as np

# 1. THE ROSETTA STONE
CODE_MAP = {
    "Request Purchase": "Request a Purchase",
    "Abandoned Chat": "Abandoned Chat",
    "Hours": "Library Hours",
    "Navigation & Wayfinding": "Library Navigation & Wayfinding",
    "Lost & Found": "Lost & Found",
    "Noise Issues": "Noise Issues",
    "Physical Accessibility": "Physical Accessibility",
    "Safety & Security": "Safety & Security",
    "Study Rooms & Reservations": "Study Rooms & Reservations",
    "Campus: Services": "Campus Services",
    "Campus Wayfinding": "Campus Wayfinding",
    "Course Reserves": "Course Reserves",
    "Faculty Instruction Support": "Faculty Instructional Support",
    "Known Item: AV": "Find a Known Item: Audiovisual (e.g., physical, digital, or streaming videos, audio recordings, music)",
    "Known Item: Books": "Find a Known Item: Books",
    "Known Item: Articles": "Find a Known Item: Journals, Periodicals, or Articles",
    "Known Item: Other": "Find a Known Item: Other (e.g., kits, maps, tools, games, slides, or non-traditional items) ",
    "Known Item: Thesis": "Find a Known Item: Theses or Dissertation",
    "Find by Author": "Find Items by Author",
    "Interlibrary Loan": "Interlibrary Loan",
    "Library Services": "Library Services",
    "Other": "Other",
    "Fines & Fees": "Fees & Fines",
    "Holds Request": "Hold Request",
    "Lost Items": "Lost Items",
    "Patron Account": "Patron Accounts",
    "Renewals": "Renewals",
    "Policies & Procedures": "Policies & Procedures",
    "Citations & Citing Sources": "Citations / Citing Sources",
    "Database Search Skills": "Database Search Skills",
    "Develop Research Topic": "Develop your research topic",
    "Evaluation Information": "Evaluating Information",
    "Finding Relevant Resources": "Finding relevant sources",
    "Managing & Organizing Information": "Managing & Organizing Information",
    "Research Strategy": "Research Strategies",
    "Borrow Tech": "Borrow Technology",
    "Connectivity & Remote Access Issues": "Connectivity & Remote Access Issues",
    "Software": "Software",
    "Tech Support": "Tech Support",
    "Website": "Website",
    "Printing & Scanning": "Printing & Scanning"
}

def clean_and_normalize(val):
    """Applies the Rosetta Stone and standardizes codes for comparison."""
    if pd.isna(val) or str(val).strip().lower() == 'nan' or not str(val).strip():
        return set()
    
    raw_list = [c.strip() for c in str(val).split(',')]
    normalized = set()
    for code in raw_list:
        # Check if the code needs translation via Rosetta Stone
        translated = CODE_MAP.get(code, code)
        # Standardize: lowercase and strip 's' to handle pluralization inconsistencies
        normalized.add(translated.lower().strip().rstrip('s'))
    return normalized

def consensus_audit_workflow(input_file, output_file):
    print(f"📂 Processing {input_file}...")
    df = pd.read_csv(input_file)

    # --- STEP 1: PRE-AUDIT CLEANUP (Splitting Logic) ---
    if 'Applied_Code_Reasoning' in df.columns and 'New_AI_Final_Code' not in df.columns:
        print("✂️ Splitting 'Applied_Code_Reasoning'...")
        split_data = df['Applied_Code_Reasoning'].str.split('|', n=1, expand=True)
        df['New_AI_Final_Code'] = split_data[0].str.strip()
        df['New_AI_Reasoning'] = split_data[1].str.strip() if len(split_data.columns) > 1 else ""

    # --- STEP 2: TIERED CLASSIFICATION ---
    def classify_tier(row):
        # Extract and Normalize Human Codes
        h_cols = ['Code 1', 'Code 2', 'Code 3']
        human = set()
        for col in h_cols:
            if col in row:
                human.update(clean_and_normalize(row[col]))
        
        # Extract and Normalize AI Codes
        ai = clean_and_normalize(row.get('New_AI_Final_Code', ''))
        
        if not human and not ai: return 'Match (Both Empty)'
        if human == ai: return 'Match'
        
        intersection = human.intersection(ai)
        
        if not intersection and human and ai:
            return 'Tier 1: Total Mismatch'
        if human.issubset(ai):
            return 'Tier 2: AI Intent Expansion'
        if ai.issubset(human):
            return 'Tier 3: AI Intent Contraction'
            
        return 'Tier 4: Complex Overlap'

    df['Audit_Tier'] = df.apply(classify_tier, axis=1)

    # --- STEP 3: GENERATE AUDIT DIFF NOTES ---
    def generate_diff(row):
        h_cols = ['Code 1', 'Code 2', 'Code 3']
        human = set()
        for col in h_cols:
            if col in row: human.update(clean_and_normalize(row[col]))
        ai = clean_and_normalize(row.get('New_AI_Final_Code', ''))
        
        added = ai - human
        missed = human - ai
        
        notes = []
        if added: notes.append(f"AI ADDED: {', '.join(added)}")
        if missed: notes.append(f"AI MISSED: {', '.join(missed)}")
        return " | ".join(notes) if notes else "No Change"

    df['Audit_Diff_Notes'] = df.apply(generate_diff, axis=1)

    # --- STEP 4: SORT AND SAVE ---
    tier_order = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap', 
                  'Tier 3: AI Intent Contraction', 'Tier 2: AI Intent Expansion', 'Match']
    df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)
    df = df.sort_values('Audit_Tier')

    df.to_csv(output_file, index=False)
    
    print("\n" + "="*30)
    print("CONSENSUS AUDIT REPORT")
    print("="*30)
    print(df['Audit_Tier'].value_counts().sort_index())
    print("="*30)
    print(f"Audit saved to: {output_file}")

if __name__ == "__main__":
    consensus_audit_workflow('CodedResults1747.csv', 'Adjudication_Master_List.csv')
