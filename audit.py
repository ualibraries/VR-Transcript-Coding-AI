import pandas as pd

# 1. ROSETTA STONE AI to Human Codebook
CODE_MAP = {
    "Request Purchase": "Request a Purchase",
    "Abandoned Chat":"Abandoned Chat"
    "Request Purchase":"Request a Purchase"
    "Hours":"Library Hours"
    "Navigation & Wayfinding":"Library Navigation & Wayfinding"
    "Lost & Found":"Lost & Found"
    "Noise Issues":"Noise Issues"
    "Physical Accessibility":"Physical Accessibility"
    "Safety & Security":"Safety & Security"
    "Study Rooms & Reservations":"Study Rooms & Reservations"
    "Campus":"Campus Services"
    "Campus Wayfinding":"Campus Wayfinding"
    "Course Reserves":"Course Reserves"
    "Faculty Instruction Support":"Faculty Instructional Support"
    "Known Item: AV":"Find a Known Item: Audiovisual (e.g., physical, digital, or streaming videos, audio recordings, music)"
    "Known Item: Books":"Find a Known Item: Books"
    "Known Item: Articles":"Find a Known Item: Journals, Periodicals, or Articles"
    "Known Item: Other":"Find a Known Item: Other (e.g., kits, maps, tools, games, slides, or non-traditional items) "
    "Known Item: Thesis":"Find a Known Item: Theses or Dissertation"
    "Known Item: Author":"Find Items by Author"
    "Interlibrary Loan":"Interlibrary Loan"
    "Library Services":"Library Services"
    "Other":"Other"
    "Fines & Fees":"Fees & Fines"
    "Holds Request":"Hold Request"
    "Lost Items":"Lost Items"
    "Patron Account":"Patron Accounts"
    "Renewals":"Renewals"
    "Policies & Procedures":"Policies & Procedures"
    "Citations & Citing Sources":"Citations / Citing Sources"
    "Database Search Skills":"Database Search Skills"
    "Develop Research Topic":"Develop your research topic"
    "Evaluation Information":"Evaluating Information"
    "Finding Relevant Resources":"Finding relevant sources"
    "Managing & Organizing Information":"Managing & Organizing Information"
    "Research Strategy":"Research Strategies"
    "Borrow Tech":"Borrow Technology"
    "Connectivity & Remote Access Issues":"Connectivity & Remote Access Issues"
    "Software":"Software"
    "Tech Support":"Tech Support"
    "Website":"Website"
    "Printing & Scanning":"Printing & Scanning"
}

# 2. Load the merged file
df_results = pd.read_csv('/content/drive/MyDrive/mergedfile.csv')

# 3. Split the single ‘Applied_Code_Reasoning' column into two
# n=1 ensures we only split at the FIRST pipe (in case reasoning contains one)
split_data = df[‘Applied_Code_Reasoning'].str.split('|', n=1, expand=True)

# 4. Assign back to your dataframe
df['AI_Final_Code'] = split_data[0].str.strip()  # The code part
df['AI_Reasoning'] = split_data[1].str.strip()   # The reasoning part

# 5. Use 'AI_Final_Code' for your Mismatch Check
def conduct_audit(df):
    results = []
    
# 6 Define your human columns (must match Excel headers exactly)
    human_cols = ['Code 1', 'Code 2', 'Code 3']
    
    for index, row in df.iterrows():
        # A. Collect all Human Codes (cleaning whitespace and ignoring empty cells)
        human_set = {str(row[col]).strip() for col in human_cols if pd.notna(row[col])}
        
        # B. Collect and Translate AI Codes
        # Splits "Code 1, Code 2" into a list
        ai_list_raw = str(row['AI_Final_Code')']).split(',')
        ai_translated = {CODE_MAP.get(c.strip(), c.strip()) for c in ai_list_raw}
        
        # C. The Intersection Test
        # We find what they AGREED on
        matches = human_set.intersection(ai_translated)        
        if matches:
            # If they share even one code, it's a 'Partial Match' 
            # If they share ALL codes, it's a 'Perfect Match'
            status = "Perfect Match" if human_set == ai_translated else "Partial Match"
        else:
            status = "Mismatch"
            
        results.append(status)
    
    df['Audit_Result'] = results
    return df

# Execute the audit on your current dataframe
df_audited = conduct_audit(df)
print(df_audited['Audit_Result'].value_counts())

