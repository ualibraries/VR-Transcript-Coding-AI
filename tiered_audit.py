import pandas as pd
import numpy as np
import re

# 1. THE ROSETTA STONE
CODE_MAP = {
    "Abandoned Chat": "Abandoned Chat",
    "Borrow Tech": "Borrow Technology",
    "Campus Services": "Campus Services",
    "Campus Wayfinding": "Campus Wayfinding",
    "Citations & Citing Sources": "Citations / Citing Sources",
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
    print(f"📂 Loading: {input_file}...")
    df = pd.read_csv(input_file)

    # --- STEP 1: SPLIT LOGIC & DEDUPLICATION ---
    if 'Applied_Code_Reasoning' in df.columns and 'New_AI_Final_Code' not in df.columns:
        # Initial split of the raw API output
        split_data = df['Applied_Code_Reasoning'].str.split('|', n=1, expand=True)

        # 1. Basic extraction and stripping
        df['New_AI_Final_Code'] = split_data[0].str.strip()
        df['New_AI_Reasoning'] = split_data[1].str.strip() if len(split_data.columns) > 1 else ""

        # 2. NEW: Deduplicate the codes
        # This handles cases like "Policies & Procedures, Policies & Procedures"
        # and turns them into a single "Policies & Procedures" entry.
        def clean_and_deduplicate(code_string):
            if pd.isna(code_string) or code_string == "":
                return code_string
            # Split by comma, remove extra whitespace, and keep unique values only
            parts = [p.strip() for p in code_string.split(',')]
            # Using a set to remove duplicates, then sorting for consistency
            unique_parts = sorted(list(set(parts)))
            return ", ".join(unique_parts)

        df['New_AI_Final_Code'] = df['New_AI_Final_Code'].apply(clean_and_deduplicate)

        # --- STEP 2: PATTERN GENERATION (New for Filtering) ---
        def get_human_pattern(row):
            codes = [str(row[c]).strip() for c in ['Code 1', 'Code 2', 'Code 3'] if pd.notna(row[c])]
            return " | ".join(sorted(codes))

        def get_ai_pattern(row):
            return str(row.get('New_AI_Final_Code', '')).strip()

        # Add these as actual columns for your CSV
        df['Human_Pattern'] = df.apply(get_human_pattern, axis=1)
        df['AI_Pattern'] = df.apply(get_ai_pattern, axis=1)

        # --- STEP 3: TIERED CLASSIFICATION ---
        def classify_tier(row):
            # We reuse our clean_and_normalize logic here
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
            added = ai - human
            missed = human - ai
            notes = []
            if added: notes.append(f"AI ADDED: {', '.join(added)}")
            if missed: notes.append(f"AI MISSED: {', '.join(missed)}")
            return " | ".join(notes) if notes else "No Change"

        df['Audit_Diff_Notes'] = df.apply(generate_diff, axis=1)

        # --- STEP 5: SORT AND SAVE ---
        # We sort by Tier first, then by the Human Pattern to group identical conflicts together
        tier_order = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap',
                      'Tier 3: AI Intent Contraction', 'Tier 2: AI Intent Expansion', 'Match']

        df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)

        # Sorting by Tier then Human_Pattern groups all "Abandoned Chat" mismatches together
        df = df.sort_values(['Audit_Tier', 'Human_Pattern'])

        # Save the file
        df.to_csv(output_file, index=False)

        # Print the terminal report
        print("\nCONSENSUS AUDIT REPORT\n" + "="*30)
        print(df['Audit_Tier'].value_counts().sort_index())
        print("="*30 + f"\n✅ Success! Adjudication file saved as: {output_file}")

if __name__ == "__main__":
    # Ensure this matches your actual pilot results filename
    INPUT_FILE = 'coded_Round5.csv'
    OUTPUT_FILE = 'Adjudication_Round5.csv'

    consensus_audit_workflow(INPUT_FILE, OUTPUT_FILE)
