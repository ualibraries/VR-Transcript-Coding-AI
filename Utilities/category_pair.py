import pandas as pd
import json
from itertools import combinations
from collections import Counter

# 1. LOAD YOUR REVISED CODEBOOK
with open('codebook_category.json', 'r') as f:
    raw_data = json.load(f)

# Handle nested JSON
codebook_list = raw_data.get('codes', []) if isinstance(raw_data, dict) else raw_data
code_to_category = {item.get('code_name'): item.get('category') for item in codebook_list if 'code_name' in item}

# 2. LOAD YOUR AI RESULTS
df = pd.read_csv('Complete_Code.csv')

# 3. MAP CODES TO UNIQUE CATEGORIES PER TRANSACTION
def get_unique_categories(code_str):
    if pd.isna(code_str): return []
    codes = [c.strip() for c in str(code_str).split(',')]
    # Using a set ensures we only count the 'Category' once even if multiple codes hit it
    categories = {code_to_category.get(code) for code in codes if code_to_category.get(code)}
    return sorted(list(categories))

df['Category_Set'] = df['New_AI_Final_Code'].apply(get_unique_categories)

# 4. GENERATE AND COUNT CO-OCCURRENCE PAIRS
# This looks for transactions with 2 or more unique categories
all_pairs = []
for cat_list in df['Category_Set']:
    if len(cat_list) > 1:
        # combinations(list, 2) creates every possible pair from the list
        for pair in combinations(cat_list, 2):
            # Sort the pair so (A, B) and (B, A) are counted together
            all_pairs.append(tuple(sorted(pair)))

# 5. FORMAT AND SAVE THE AUDIT
pair_counts = Counter(all_pairs).most_common()
pair_df = pd.DataFrame(pair_counts, columns=['Pair', 'Frequency'])

# Split the 'Pair' tuple into readable columns
if not pair_df.empty:
    pair_df[['Category A', 'Category B']] = pd.DataFrame(pair_df['Pair'].tolist(), index=pair_df.index)
    pair_df = pair_df[['Category A', 'Category B', 'Frequency']]

# 6. SAVE TO CSV
pair_df.to_csv('AI_Category_Pairing_Audit.csv', index=False)

print("✅ Pairing Audit Complete. Results saved to 'AI_Category_Pairing_Audit.csv'")
print(pair_df.head(10))
