import pandas as pd

# Load your batch file
file_path = 'Coded_Batch_1521_to_2521.csv'
df = pd.read_csv(file_path)

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
output_path = 'Cleaned_Batch_0_to_1000.csv'
df.to_csv(output_path, index=False)

print(f"✅ Processing complete. {len(df)} rows split and normalized.")
print(f"📁 File saved to: {output_path}")
