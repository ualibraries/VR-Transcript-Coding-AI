import pandas as pd

# 1. Load your Adjusted Audit file
# (Ensure this matches your actual file name)
AUDIT_FILE = "/content/drive/MyDrive/Colab_Outputs/Adjudication_Complete.csv"
df = pd.read_csv(AUDIT_FILE)

# 2. Filter for the "Edge Cases" (Tier 1 and Tier 4)
# This captures the 181 Mismatches and 100 Complex Overlaps
triage_tiers = ['Tier 1: Total Mismatch', 'Tier 4: Complex Overlap']
df_triage = df[df['Audit_Tier'].isin(triage_tiers)].copy()

# 3. Add the Expert Decision Columns
# We leave these blank for your human experts to fill in
df_triage['Expert_Final_Code'] = ""
df_triage['Expert_Reasoning'] = ""
df_triage['Decision_Category'] = "" # e.g., "AI was right", "Human was right", "Both valid"

# 4. Reorder columns for easier reading
# Placing AI_Thoughts next to the Expert Decision columns is key
final_columns = [
    'StudyID',
    'Institution',
    'ID',
    'Audit_Tier', 
    'Transcript', 
    'Human_Pattern', 
    'AI_Pattern', 
    'Expert_Final_Code', 
    'Expert_Reasoning', 
    'AI_Thoughts', 
    'Decision_Category'
]

# Ensure only existing columns are used to avoid errors
df_triage = df_triage[[col for col in final_columns if col in df_triage.columns]]

# 5. Save the Triage File
output_path = "/content/drive/MyDrive/Colab_Outputs/Expert_Triage_281.csv"
df_triage.to_csv(output_path, index=False)

print(f"✅ Success! Created triage file with {len(df_triage)} rows.")
print(f"📂 Location: {output_path}")
