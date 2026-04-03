import pandas as pd
import json

# 1. LOAD YOUR REVISED CODEBOOK
with open('codebook_category.json', 'r') as f:
    raw_data = json.load(f)

# STRUCTURAL CHECK: If the JSON is a dict, find the list inside it
if isinstance(raw_data, dict):
    # Try to find the list under 'codes', 'categories', or similar
    # Adjust 'codes' below if your JSON key is different
    codebook_list = raw_data.get('codes', [])
else:
    codebook_list = raw_data

# 2. CREATE THE LOOKUP DICTIONARY
# This converts the list into a simple { "Code Name": "Category" } map
# Filter out items that do not have both 'code_name' and 'category' keys
code_to_category = {item['code_name']: item['category'] for item in codebook_list if 'code_name' in item and 'category' in item}

# 3. LOAD YOUR AI RESULTS
df = pd.read_csv('Complete_Code.csv')

# 4. PROCESS THE MULTI-INTENT CODES
# We ensure everything is a string, split by comma, and stripped of whitespace
df['Code_List'] = df['New_AI_Final_Code'].astype(str).str.split(',').apply(
    lambda x: [i.strip() for i in x] if isinstance(x, list) else []
)
exploded_df = df.explode('Code_List')

# 5. MAP CODES TO CATEGORIES
exploded_df['Parent_Category'] = exploded_df['Code_List'].map(code_to_category)

# 6. GENERATE THE AUDIT REPORT
category_counts = exploded_df['Parent_Category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Total Instances']

# 7. ADD STUDY IDs (The "Pickle-Buster" Column)
# This groups all Study IDs into a single cell for each category for easy auditing
study_id_map = exploded_df.groupby('Parent_Category')['StudyID'].apply(
    lambda x: ', '.join(x.astype(str))
).reset_index()

# Merge the counts and the ID lists
final_report = pd.merge(category_counts, study_id_map, left_on='Category', right_on='Parent_Category', how='left')

# 8. SAVE RESULTS
final_report.to_csv('AI_Category_Workload_Audit.csv', index=False)

print("✅ Category Audit Complete. Check 'AI_Category_Workload_Audit.csv' for results.")
