import pandas as pd

# 1. Load your data (Change 'coding_results.csv' to your actual file name)
# If your file is tab-separated, use sep='\t'
file_path = "Coded_Batch_10_to_110.csv"
df = pd.read_csv(file_path)

# 2. Define a helper function to count words safely
def count_words(text):
    if pd.isna(text):
        return 0
    # Split by whitespace to get individual words
    return len(str(text).split())

# 3. Apply the word count to the AI_Thoughts column
df['Word_Count'] = df['AI_Thoughts'].apply(count_words)

# 4. Filter for rows where the word count strictly exceeds 550 words
over_limit_df = df[df['Word_Count'] > 550]

# 5. Extract just the Study IDs
flagged_study_ids = over_limit_df['StudyID'].tolist()

# 6. Output the results
print(f"Found {len(flagged_study_ids)} study ID(s) exceeding 550 words:\n")
for study_id in flagged_study_ids:
    print(study_id)

# Optional: Save the flagged rows to a new file for easy review
# over_limit_df.to_csv('flagged_studies.csv', index=False)
