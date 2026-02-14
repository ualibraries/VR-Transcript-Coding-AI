import pandas as pd

# 1. ROSETTA STONE
CODE_MAP = {
    "Request Purchase": "Request a Purchase",
    "Abandoned Chat":"Abandoned Chat",
    "Hours":"Library Hours",
    "Navigation & Wayfinding":"Library Navigation & Wayfinding",
    "Lost & Found":"Lost & Found",
    "Noise Issues":"Noise Issues",
    "Physical Accessibility":"Physical Accessibility",
    "Safety & Security":"Safety & Security",
    "Study Rooms & Reservations":"Study Rooms & Reservations",
    "Campus: Services":"Campus Services",
    "Campus Wayfinding":"Campus Wayfinding",
    "Course Reserves":"Course Reserves",
    "Faculty Instruction Support":"Faculty Instructional Support",
    "Faculty Instructional Support":"Faculty Instructional Support", # Added to be safe
    "Known Item: AV":"Find a Known Item: Audiovisual (e.g., physical, digital, or streaming videos, audio recordings, music)",
    "Known Item: Books":"Find a Known Item: Books",
    "Known Item: Articles":"Find a Known Item: Journals, Periodicals, or Articles",
    "Known Item: Other":"Find a Known Item: Other (e.g., kits, maps, tools, games, slides, or non-traditional items) ",
    "Known Item: Thesis":"Find a Known Item: Theses or Dissertation",
    "Known Item: Author":"Find Items by Author",
    "Interlibrary Loan":"Interlibrary Loan",
    "Library Services":"Library Services",
    "Other":"Other",
    "Fines & Fees":"Fees & Fines",
    "Holds Request":"Hold Request",
    "Lost Items":"Lost Items",
    "Patron Account":"Patron Accounts",
    "Renewals":"Renewals",
    "Policies & Procedures":"Policies & Procedures",
    "Citations & Citing Sources":"Citations / Citing Sources",
    "Database Search Skills":"Database Search Skills",
    "Develop Research Topic":"Develop your research topic",
    "Evaluation Information":"Evaluating Information",
    "Finding Relevant Resources":"Finding relevant sources",
    "Managing & Organizing Information":"Managing & Organizing Information",
    "Research Strategy":"Research Strategies",
    "Borrow Tech":"Borrow Technology",
    "Connectivity & Remote Access Issues":"Connectivity & Remote Access Issues",
    "Software":"Software",
    "Tech Support":"Tech Support",
    "Website":"Website",
    "Printing & Scanning":"Printing & Scanning"
}

# 2. Load the file
df_results = pd.read_csv('/content/drive/My Drive/CodedResults1747.csv')

# 3. Split the single ‘Applied_Code_Reasoning' column
split_data = df_results['Applied_Code_Reasoning'].str.split('|', n=1, expand=True)

# 4. Assign back
df_results['AI_Final_Code'] = split_data[0].str.strip()
df_results['AI_Reasoning'] = split_data[1].str.strip()

# 5. Define Human Columns
human_cols = ['Code 1', 'Code 2', 'Code 3']
results = []

# 6. The Corrected Audit Loop
for index, row in df_results.iterrows():
    # A. Clean Human Codes
    human_set = {
        str(row[col]).strip().lower().rstrip('s') 
        for col in human_cols if pd.notna(row[col]) and str(row[col]).strip() != ""
    }

    # B. Clean AI Codes
    # We map them FIRST, then strip/lower/rstrip
    ai_raw = str(row['AI_Final_Code']).split(',')
    ai_translated = {
        CODE_MAP.get(c.strip(), c.strip()).lower().rstrip('s') 
        for c in ai_raw if c.strip() != ""
    }

    # C. Intersection
    matches = human_set.intersection(ai_translated)

    if matches:
        if human_set == ai_translated:
            status = "Perfect Match"
        else:
            status = "Partial Match"
    else:
        status = "Mismatch"
    
    results.append(status)

# 7. Update and Show
df_results['Audit_Result'] = results
print("--- UPDATED AUDIT TOTALS ---")
print(df_results['Audit_Result'].value_counts())
