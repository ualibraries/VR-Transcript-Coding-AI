import pandas as pd
import numpy as np
import re

# 1. THE ROSETTA STONE
CODE_MAP = {
    "Request Purchase": "Request a Purchase",
    "Abandoned Chat": "Abandoned Chat",
    "System Test": "System Test",
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
    "Known Item: Other": "Find a Known Item: Other (e.g., kits, maps, tools, games, slides, or non-traditional items)",
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
    if pd.isna(val) or str(val).strip().lower() in ['nan', '']:
        return set()
    
    normalized = set()
    full_string = str(val).lower().strip()
    
    # Iterate through the Rosetta Stone to find matches
    for short_key, long_description in CODE_MAP.items():
        sk_clean = short_key.lower().strip()
        ld_clean = long_description.lower().strip()
        
        # If EITHER the short key or the long description is in the text
        if ld_clean in full_string or sk_clean in full_string:
            # Map to the standardized Short Key ID
            final_id = re.sub(r'[^a-zA-Z0-9]', '', sk_clean).rstrip('s')
            normalized.add(final_id)
            
    if not normalized:
        raw_list = [c.strip() for c in full_string.split(',')]
        for entry in raw_list:
            clean = re.sub(r'[^a-zA-Z0-9]', '', entry).rstrip('s')
            normalized.add(clean)
            
    return normalized

def consensus_audit_workflow(input_file, output_file):
    print(f"📂 Processing: {input_file}...")
    df = pd.read_csv(input_file)

    # Split logic
    if 'Applied_Code_Reasoning' in df.columns and 'New_AI_Final_Code' not in df.columns:
        split_data = df['Applied_Code_Reasoning'].str.split('|', n=1, expand=True)
        df['New_AI_Final_Code'] = split_data[0].str.strip()
        df['New_AI_Reasoning'] = split_data[1].str.strip() if len(split_data.columns) > 1 else ""

    def classify_tier(row):
        h_cols = ['Code 1', 'Code 2', 'Code 3']
        human = set()
        for col in h_cols:
            if col in row: human.update(clean_and_normalize(row[col]))
        
        ai = clean_and_normalize(row.get('New_AI_Final_Code', ''))
        
        if not human and not ai: return 'Match (Both Empty)'
        if human == ai: return 'Match'
        
        intersection = human.intersection(ai)
        if not intersection and human and ai: return 'Tier 1: Total Mismatch'
        if human.issubset(ai): return 'Tier 2: AI Intent Expansion'
        if ai.issubset(human): return 'Tier 3: AI Intent Contraction'
        return 'Tier 4: Complex Overlap'

    df['Audit_Tier'] = df.apply(classify_tier, axis=1)

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

    tier_order = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap', 
                  'Tier 3: AI Intent Contraction', 'Tier 2: AI Intent Expansion', 'Match']
    df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)
    df = df.sort_values('Audit_Tier')

    df.to_csv(output_file, index=False)
    print("\nCONSENSUS AUDIT REPORT\n" + "="*30)
    print(df['Audit_Tier'].value_counts().sort_index())
    print("="*30 + f"\nSaved to: {output_file}")

if __name__ == "__main__":
    consensus_audit_workflow('coded_results_1500pilot.csv', 'Adjudication_Master_List_Final.csv')
