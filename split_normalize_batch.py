import pandas as pd
import os
import sys
from google.colab import drive

# 1. Mount Drive
drive.mount('/content/drive')

# 2. Setup Pathing
DRIVE_MODULES_FOLDER = 'AZ_Only'
MODULES_FULL_PATH = os.path.join('/content/drive/MyDrive', DRIVE_MODULES_FOLDER)
if MODULES_FULL_PATH not in sys.path:
    sys.path.append(MODULES_FULL_PATH)

# Load your batch file
INPUT_FILE = '/content/drive/MyDrive/AZ_Only/Coded_AZ_Batch_100_to_300.csv'
df = pd.read_csv(INPUT_FILE)

def split_and_normalize(row):
    raw_content = str(row['New_AI_Final_Code'])

    # Initialize defaults
    codes = raw_content
    reasoning = ""

    # 1. Split the codes from the reasoning using the pipe delimiter
    if '|' in raw_content:
        parts = raw_content.split('|', 1)
        codes = parts[0].strip()
        reasoning_blob = parts[1].strip()

        # 2. Strip the "[Reasoning: " prefix and "]" suffix
        # Removing '[Reasoning: ' (12 chars) and ']' (last char)
        if reasoning_blob.startswith('[Reasoning:'):
            reasoning = reasoning_blob.replace('[Reasoning:', '', 1).rstrip(']').strip()
        else:
            reasoning = reasoning_blob

    return codes, reasoning

# Apply the function to create the two new columns
df[['AI_Final_Code', 'AI_Reasoning']] = df.apply(
    lambda x: pd.Series(split_and_normalize(x)), axis=1
)

# Optional: Normalize the codes by ensuring consistent spacing after commas
df['AI_Final_Code'] = df['AI_Final_Code'].str.replace(', ', ',').str.replace(',', ', ')

# Save the cleaned file
output_path = '/content/drive/MyDrive/AZ_Only/Cleaned/Cleaned_AZ_Batch_100_to_300.csv'
df.to_csv(output_path, index=False)

print(f"✅ Processing complete. {len(df)} rows split and normalized.")
print(f"📁 File saved to: {output_path}")
