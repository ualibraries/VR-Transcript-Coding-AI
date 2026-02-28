import pandas as pd
import re
import os

# 1. THE ROSETTA STONE
CODE_MAP = {
    "Abandoned Chat": "Abandoned Chat",
    "Borrow Tech": "Borrow Technology",
    "Campus Services": "Campus Services",
    "Campus Wayfinding": "Campus Wayfinding",
    "Citations / Citing Sources": "Citations / Citing Sources",
    "Connectivity & Remote Access Issues": "Connectivity & Remote Access Issues",
    "Course Reserves": "Course Reserves",
    "Database Search Skills": "Database Search Skills",
    "Develop Research Topic": "Develop your research topic",
    "Evaluation Information": "Evaluating Information",
    "Faculty Instruction Support": "Faculty Instructional Support",
    "Find by Author": "Find Items by Author",
    "Finding Relevant Resources": "Finding relevant sources",
    "Fines & Fees": "Fees & Fines",
    "Hold Request": "Hold Request",
    "Hours": "Library Hours",
    "Interlibrary Loan": "Interlibrary Loan",
        # Singular (AI's favorite)
    "Known Item: Article": "Find a Known Item: Journals, Periodicals, or Articles",
    "Known Item: Book": "Find a Known Item: Books",
         # plural (safety net)
    "Known Item: Articles": "Find a Known Item: Journals, Periodicals, or Articles",
    "Known Item: Books": "Find a Known Item: Books",
    "Known Item: AV": "Find a Known Item: Audiovisual (e.g., physical, digital, or streaming videos, audio recordings, music)",
    "Known Item: Other": "Find a Known Item: Other (e.g., kits, maps, tools, games, slides, or non-traditional items)",
    "Known Item: Thesis": "Find a Known Item: Theses or Dissertation",
    "Library Services": "Library Services",
    "Lost & Found": "Lost & Found",
    "Lost Items": "Lost Items",
    "Managing & Organizing Information": "Managing & Organizing Information",
    "Navigation & Wayfinding": "Library Navigation & Wayfinding",
    "Noise Issues": "Noise Issues",
    "Other": "Other",
    "Patron Account": "Patron Accounts",
    "Physical Accessibility": "Physical Accessibility",
    "Policies & Procedures": "Policies & & Procedures",
    "Printing & Scanning": "Printing & Scanning",
    "Renewals": "Renewals",
    "Research Strategy": "Research Strategies",
    "Safety & Security": "Safety & Security",
    "Software": "Software",
    "Study Rooms & Reservations": "Study Rooms & Reservations",
    "System Test": "System Test",
    "Tech Support": "Tech Support",
    "Website": "Website",
    "Request Purchase": "Request a Purchase"
}

def clean_and_normalize(val):
    if pd.isna(val) or str(val).strip().lower() in ['nan', '']:
        return set()
    normalized = set()
    
    # Helper for "Fuzzy Matching" (removes & / and plurals)
    def fuzzy(s):
        return re.sub(r'[^a-zA-Z0-9]', '', str(s).lower()).rstrip('s')

    raw_val = str(val).lower().strip()
    # Isolate just the code part (before the pipe)
    code_section = raw_val.split("|")[0]
    clean_input = fuzzy(code_section)

    for short_key, long_description in CODE_MAP.items():
        sk_clean = fuzzy(short_key)
        ld_clean = fuzzy(long_description)
        if sk_clean in clean_input or ld_clean in clean_input:
            normalized.add(short_key)

    if not normalized and clean_input != "":
        normalized.add(clean_input)
    return normalized

def consensus_audit_workflow(input_file, output_file):
    print(f"📂 Loading: {input_file}...")
    df = pd.read_csv(input_file)

    # --- STEP 1: ENHANCED SPLIT LOGIC (GEMINI 3 READY) ---
    if 'Applied_Code_Reasoning' in df.columns:
        # We now look for AI_Thoughts as well
        # Expected Format: Code | Reasoning | Thoughts
        split_data = df['Applied_Code_Reasoning'].str.split('|', n=2, expand=True)

        df['New_AI_Final_Code'] = split_data[0].str.strip()
        df['New_AI_Reasoning'] = split_data[1].str.strip() if len(split_data.columns) > 1 else ""
        
        # --- NEW: CATCH THE THOUGHTS ---
        if len(split_data.columns) > 2:
            df['AI_Thoughts'] = split_data[2].str.strip()
        elif 'AI_Thoughts' not in df.columns:
            df['AI_Thoughts'] = "No thoughts captured"

        # Deduplicate the codes (Standard Cleanup)
        def clean_and_deduplicate(code_string):
            if pd.isna(code_string) or code_string == "": return code_string
            parts = [p.strip() for p in str(code_string).split(',')]
            return ", ".join(sorted(list(set(parts))))

        df['New_AI_Final_Code'] = df['New_AI_Final_Code'].apply(clean_and_deduplicate)

        # --- STEP 2: PATTERN GENERATION ---
        def get_human_pattern(row):
            codes = [str(row[c]).strip() for c in ['Code 1', 'Code 2', 'Code 3'] if pd.notna(row[c])]
            return " | ".join(sorted(codes))

        df['Human_Pattern'] = df.apply(get_human_pattern, axis=1)
        df['AI_Pattern'] = df.apply(lambda x: str(x.get('New_AI_Final_Code', '')).strip(), axis=1)

        # --- STEP 3: TIERED CLASSIFICATION ---
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

        # --- STEP 4: GENERATE DIFF NOTES ---
        def generate_diff(row):
            h_cols = ['Code 1', 'Code 2', 'Code 3']
            human = set()
            for col in h_cols:
                if col in row: human.update(clean_and_normalize(row[col]))
            ai = clean_and_normalize(row.get('New_AI_Final_Code', ''))
            added, missed = ai - human, human - ai
            notes = []
            if added: notes.append(f"AI ADDED: {', '.join(added)}")
            if missed: notes.append(f"AI MISSED: {', '.join(missed)}")
            return " | ".join(notes) if notes else "No Change"

        df['Audit_Diff_Notes'] = df.apply(generate_diff, axis=1)

        # --- STEP 5: SAVE & INVESTIGATE ---
        tier_order = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap',
                      'Tier 3: AI Intent Contraction', 'Tier 2: AI Intent Expansion', 'Match']
        df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)
        df = df.sort_values(['Audit_Tier', 'Human_Pattern'])

        # Save the full file
        df.to_csv(output_file, index=False)

        # --- NEW: SAVE TIER 4 INVESTIGATION AUTOMATICALLY ---
        t4_df = df[df['Audit_Tier'] == 'Tier 4: Complex Overlap'].copy()
        if not t4_df.empty:
            t4_df.to_csv('Tier4_Investigation.csv', index=False)
            print(f"🕵️ Created investigation file with {len(t4_df)} rows.")

        print("\nCONSENSUS AUDIT REPORT\n" + "="*30)
        print(df['Audit_Tier'].value_counts().sort_index())
        print("="*30 + f"\n✅ Success! Adjudication saved as: {output_file}")

if __name__ == "__main__":
    INPUT_FILE = 'Results_3_Flash_D.csv'
    OUTPUT_FILE = 'Adjudication_Flash3D.csv'
    consensus_audit_workflow(INPUT_FILE, OUTPUT_FILE)
