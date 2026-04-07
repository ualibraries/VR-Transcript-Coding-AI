import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load your adjudicated data
df = pd.read_csv("adjudicated_transcripts.csv")

# 2. Identify the column containing your codes (without reasoning)
# Adjust 'Final_Codes' to match your actual column name
code_column = 'Final_Codes'

# 3. Calculate "Intent Count" (Number of codes per row)
# We split the string by commas and count the items in the resulting list
df['Intent_Count'] = df[code_column].apply(
    lambda x: len([c.strip() for c in str(x).split(',') if c.strip()])
)

# 4. (Optional) Calculate "Word Count" if you have a transcript column
# This allows you to see if long chats are actually complex or just wordy
if 'Transcript_Text' in df.columns:
    df['Word_Count'] = df['Transcript_Text'].str.split().str.len()
    df['Intent_Density_per_100_Words'] = (df['Intent_Count'] / df['Word_Count']) * 100

# 5. Generate Summary Statistics
print("--- Intent Complexity Summary ---")
print(f"Average Intents per Chat: {df['Intent_Count'].mean():.2f}")
print(f"Max Intents in a Single Chat: {df['Intent_Count'].max()}")
print("\nDistribution of Intent Counts:")
print(df['Intent_Count'].value_counts(normalize=True).sort_index() * 100)

# 6. Visualize the Distribution
plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='Intent_Count', palette='viridis')
plt.title("Distribution of Intent Complexity (Codes per Transcript)")
plt.xlabel("Number of Unique Intents (Codes)")
plt.ylabel("Number of Transcripts")
plt.savefig("intent_distribution.png")

# 7. Save the results back to a CSV for your own records
df.to_csv("transcripts_with_complexity_metrics.csv", index=False)
