import pandas as pd
import re

# 1. Load your master file
df = pd.read_csv('Complete_Code.csv')

# --- ROBUST FILTERING FUNCTION ---
def nuclear_filter(exploded_df, column_name):
    # This captures 'abandoned', 'Abandoned', 'abandoned chat', 'Abandoned Chat ', etc.
    # It also handles hidden whitespace and non-breaking spaces (\xa0)
    
    # Create a mask for rows that DO NOT contain 'abandon'
    mask = ~exploded_df[column_name].str.contains('abandon', case=False, na=False, regex=True)
    
    # Diagnostic: Let's see what we are about to drop
    dropped_values = exploded_df[~mask][column_name].unique()
    print(f"🚫 Removing these variants from {column_name}: {dropped_values}")
    
    return exploded_df[mask]

# --- PART 1: AI CODE ANALYSIS ---
def split_codes(val):
    if pd.isna(val): return []
    # Split by comma or semicolon just in case
    return [c.strip() for c in re.split(r'[,;]', str(val)) if c.strip()]

df['AI_Code_List'] = df['New_AI_Final_Code'].apply(split_codes)
ai_exploded = df.explode('AI_Code_List')

# Apply the Nuclear Filter
ai_filtered = nuclear_filter(ai_exploded, 'AI_Code_List')

# Calculate Top 10 on the CLEAN data
ai_counts = ai_filtered['AI_Code_List'].value_counts().head(10).reset_index()
ai_counts.columns = ['Transaction Code', 'Count']
ai_counts['Rank'] = ai_counts.index + 1
# Percentage is now calculated against the 'Active' workload only
ai_counts['Percentage'] = (ai_counts['Count'] / len(ai_filtered) * 100).round(2)

# Consistency Check
num_inst = df['Institution'].nunique()
inst_per_ai = ai_filtered.groupby('AI_Code_List')['Institution'].nunique()
ai_counts['Consistent Across All Inst'] = ai_counts['Transaction Code'].map(
    lambda x: "Yes" if inst_per_ai.get(x, 0) == num_inst else "No"
)

ai_counts.to_csv('AI_Top_10_No_Abandoned.csv', index=False)


# --- PART 2: HUMAN CODE ANALYSIS ---
def collect_human_codes(row):
    return [str(row[c]).strip() for c in ['Code 1', 'Code 2', 'Code 3'] if pd.notna(row[c])]

df['Human_Code_List'] = df.apply(collect_human_codes, axis=1)
human_exploded = df.explode('Human_Code_List')

# Apply the Nuclear Filter
human_filtered = nuclear_filter(human_exploded, 'Human_Code_List')

# Calculate Top 10 on the CLEAN data
human_counts = human_filtered['Human_Code_List'].value_counts().head(10).reset_index()
human_counts.columns = ['Transaction Code', 'Count']
human_counts['Rank'] = human_counts.index + 1
human_counts['Percentage'] = (human_counts['Count'] / len(human_filtered) * 100).round(2)

# Consistency Check
inst_per_human = human_filtered.groupby('Human_Code_List')['Institution'].nunique()
human_counts['Consistent Across All Inst'] = human_counts['Transaction Code'].map(
    lambda x: "Yes" if inst_per_human.get(x, 0) == num_inst else "No"
)

human_counts.to_csv('Human_Top_10_No_Abandoned.csv', index=False)

print("\n📊 Success! Generated: AI_Top_10_No_Abandoned.csv and Human_Top_10_No_Abandoned.csv")
