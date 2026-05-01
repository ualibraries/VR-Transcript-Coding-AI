import pandas as pd
import os

# 1. Setup paths
# Since we are working with your combined data, use your Master Output path
input_file = '/content/drive/MyDrive/34Batch/Combined/AZCombine/azcombine.csv'
output_file = '/content/drive/MyDrive/34Batch/Combined/AZCombine/library_AZ2.csv'

# 2. Load the Master Data
df = pd.read_csv(input_file)

# 3. Filter for "Library Services"
# We search the 'AI_Final_Code' column specifically.
# 'case=False' handles any capitalization shifts, and 'na=False' skips empty rows.
filter_mask = df['AI_Final_Code'].str.contains('Library Services', case=False, na=False)
campus_df = df[filter_mask].copy()

# 4. Select only the columns needed for your Gem
target_columns = [
    'StudyID',
    'OriginalTranscript',
    'AI_Thoughts',
    'AI_Reasoning',
    'AI_Final_Code'
]

# Ensure we only grab columns that exist (safety check)
final_df = campus_df[[col for col in target_columns if col in campus_df.columns]]

# 5. Save to a new CSV for Gem processing
final_df.to_csv(output_file, index=False)

print(f"✅ Success! Found {len(final_df)} transcripts matching 'Campus Services'.")
print(f"📂 File saved for your Gem at: {output_file}")
