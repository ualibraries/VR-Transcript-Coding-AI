import pandas as pd
import json

# 1. LOAD YOUR REVISED CODEBOOK
with open('codebook_category.json', 'r') as f:
    raw_data = json.load(f)

# Handle potential nested JSON structure
if isinstance(raw_data, dict):
    codebook_list = raw_data.get('codes', []) 
else:
    codebook_list = raw_data

# 2. CREATE LOOKUP MAPS
# Map 1: {Code -> Category} (for processing the CSV)
code_to_category = {item.get('code_name'): item.get('category') for item in codebook_list if 'code_name' in item}

# Map 2: {Category -> List of all Codes} (for the final report)
category_to_all_codes = {}
for item in codebook_list:
    cat = item.get('category')
    code = item.get('code_name')
    if cat and code:
        if cat not in category_to_all_codes:
            category_to_all_codes[cat] = []
        category_to_all_codes[cat].append(code)

# Convert list of codes to a single comma-separated string
cat_all_codes_str = {k: ", ".join(v) for k, v in category_to_all_codes.items()}

# 3. LOAD YOUR AI RESULTS
df = pd.read_csv('Complete_Code.csv')

# 4. PROCESS THE MULTI-INTENT CODES
df['Code_List'] = df['New_AI_Final_Code'].astype(str).str.split(',').apply(
    lambda x: [i.strip() for i in x] if isinstance(x, list) else []
)
exploded_df = df.explode('Code_List')

# 5. MAP CODES TO CATEGORIES
exploded_df['Parent_Category'] = exploded_df['Code_List'].map(code_to_category)

# 6. AGGREGATE COUNTS & STUDY IDs
# Count instances per category
category_counts = exploded_df['Parent_Category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Total Instances']

# Collect Study IDs per category
study_id_map = exploded_df.groupby('Parent_Category')['StudyID'].apply(
    lambda x: ', '.join(x.unique().astype(str))
).reset_index()
study_id_map.columns = ['Category', 'Associated Study IDs']

# 7. MERGE EVERYTHING & ADD THE "ALL CODES" FIELD
final_report = pd.merge(category_counts, study_id_map, on='Category', how='left')

# Map the full list of category codes to the report
final_report['Codes in this Category'] = final_report['Category'].map(cat_all_codes_str)

# Calculate Percentage based on total instances
total_intents = final_report['Total Instances'].sum()
final_report['% of Total Workload'] = (final_report['Total Instances'] / total_intents * 100).round(2)

# 8. SAVE RESULTS
final_report.to_csv('AI_Category_Workload_Audit_with_Codes.csv', index=False)

print("✅ Enhanced Category Audit Complete. Report saved to 'AI_Category_Workload_Audit_with_Codes.csv'")
