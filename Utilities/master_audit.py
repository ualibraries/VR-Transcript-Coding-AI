import pandas as pd
import re

# 1. Load your master file
df = pd.read_csv('Complete_Code.csv')

# --- DATA CLEANING ---
def collect_human_data(row):
    codes = []
    # Using 'Code 1', 'Code 2', and 'Code 3' for the Human analysis
    for col in ['Code 1', 'Code 2', 'Code 3']:
        val = str(row[col]).strip()
        # Filter out nulls and 'abandoned' categories
        if pd.notna(row[col]) and val.lower() != 'nan' and not re.search('abandon', val, re.IGNORECASE):
            codes.append(val)
    return codes

# Apply the collection logic
df['Human_Code_List'] = df.apply(collect_human_data, axis=1)

# 2. Explode the data (One row per Code/Study ID pair)
audit_df = df.explode('Human_Code_List')
audit_df = audit_df[audit_df['Human_Code_List'].notna()] # Drop empty entries

# 3. Aggregate results for EVERY code category
# This creates a full list regardless of rank
master_stats = audit_df.groupby('Human_Code_List').agg(
    Count=('Human_Code_List', 'count'),
    Study_IDs=('StudyID', lambda x: ', '.join(x.astype(str)))
).reset_index()

# 4. Calculate Percentage based on total active codes
total_codes_found = master_stats['Count'].sum()
master_stats['Percentage_of_Total'] = (master_stats['Count'] / total_codes_found * 100).round(2)

# 5. Final Formatting
# Sorting alphabetically by the Category Name to make it easy to find specific codes
master_stats = master_stats.sort_values(by='Human_Code_List').reset_index(drop=True)

master_stats.columns = ['Transaction Code Category', 'Total Count', 'Associated Study IDs', 'Percentage of Total']

# 6. Save to CSV
master_stats.to_csv('Full_Code_Category_Audit.csv', index=False)

print(f"✅ Master Audit Complete.")
print(f"Total unique code categories found: {len(master_stats)}")
print(f"Total instances of labor captured: {total_codes_found}")
print("Output saved to: 'Full_Code_Category_Audit.csv'")
