import pandas as pd
import re

# 1. Load your master file
df = pd.read_csv('/content/drive/MyDrive/Colab_Outputs/Adjudicated_April.csv')

# --- NORMALIZATION & CLEANING LOGIC ---
# Define the mapping of common "drifts" to the "Gold Standard"
normalization_map = {
    "Patron Accounts": "Patron Account",
    "Finding relevant sources": "Finding Relevant Resources",
    "Finding relevant resources": "Finding Relevant Resources",
    "Borrow Techs": "Borrow Tech"
}

def split_and_normalize(val):
    if pd.isna(val): return []
    # 1. Split by comma or semicolon
    raw_codes = [c.strip() for c in re.split(r'[,;]', str(val)) if c.strip()]
    
    # 2. Normalize and Filter (Abandon check)
    clean_codes = []
    for c in raw_codes:
        # Apply the map if it exists, otherwise keep original
        normalized = normalization_map.get(c, c)
        # Only add if it's not an 'abandon' code
        if not re.search('abandon', normalized, re.IGNORECASE):
            clean_codes.append(normalized)
            
    return clean_codes

# Apply the combined logic to create the list for exploding
df['AI_Code_List'] = df['New_AI_Final_Code'].apply(split_and_normalize)

# 2. Explode the data (One row per Code/Study ID pair)
ai_audit_df = df.explode('AI_Code_List')
# Drop any rows that became empty lists
ai_audit_df = ai_audit_df[ai_audit_df['AI_Code_List'].notna()]

# 3. Aggregate results for EVERY AI code category
# Ensure StudyID is treated as a string for joining
master_ai_stats = ai_audit_df.groupby('AI_Code_List').agg(
    Total_Count=('AI_Code_List', 'count'),
    Study_IDs=('StudyID', lambda x: ', '.join(x.astype(str)))
).reset_index()

# 4. Calculate Percentage based on total active AI codes
total_ai_instances = master_ai_stats['Total_Count'].sum()
master_ai_stats['Percentage_of_Total'] = (master_ai_stats['Total_Count'] / total_ai_instances * 100).round(2)

# 5. Final Formatting (Alphabetical by Category)
master_ai_stats = master_ai_stats.sort_values(by='AI_Code_List').reset_index(drop=True)
master_ai_stats.columns = ['AI Transaction Category', 'Total Count', 'Associated Study IDs', 'Percentage of Total']

# 6. Save to CSV
master_ai_stats.to_csv('Master_AI_Code_Audit.csv', index=False)

print(f"✅ Master AI Audit Complete.")
print(f"Total unique AI categories identified: {len(master_ai_stats)}")
print(f"Total instances of AI-captured labor: {total_ai_instances}")
