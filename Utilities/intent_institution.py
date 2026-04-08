import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load your adjudicated data
df = pd.read_csv("/content/drive/MyDrive/Colab_Outputs/Adjudication_April_X.csv")

# 2. Setup Column Names
code_column = 'New_AI_Final_Code'
group_column = 'Institution'  # The column for your five schools

# 3. Calculate "Intent Count" (Number of codes per row)
df['Intent_Count'] = df[code_column].apply(
    lambda x: len([c.strip() for c in str(x).split(',') if c.strip()])
)

# 4. Generate Institutional Summary Statistics
# This shows the average and max complexity for each school
inst_summary = df.groupby(group_column)['Intent_Count'].agg(['mean', 'max', 'count']).rename(
    columns={'mean': 'Avg_Intents', 'max': 'Max_Intents', 'count': 'Total_Transactions'}
).reset_index()

# 5. Generate Intent Distribution % by Institution
# This calculates what % of chats at each school had 1, 2, 3, etc. intents
distribution = pd.crosstab(df[group_column], df['Intent_Count'], normalize='index') * 100

print("--- Institution Complexity Summary ---")
print(inst_summary)

# 6. Visualize: Average Complexity Comparison
plt.figure(figsize=(10, 6))
sns.barplot(data=inst_summary.sort_values('Avg_Intents', ascending=False), 
            x=group_column, y='Avg_Intents', palette='magma')
plt.title("Comparison of Average Intent Density by Institution")
plt.ylabel("Avg Intents Per Chat")
plt.xlabel("Institution")
plt.xticks(rotation=45)
plt.savefig("avg_intent_by_institution.png")

# 7. Visualize: The Complexity Heatmap
# This shows where the "Service Nexus" is most concentrated
plt.figure(figsize=(12, 8))
sns.heatmap(distribution, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': '% of Chats'})
plt.title("Intent Count Distribution (%) by Institution")
plt.xlabel("Number of Unique Intents")
plt.ylabel("Institution")
plt.savefig("institution_complexity_heatmap.png")

# 8. Save the detailed results
df.to_csv("transcripts_with_institution_metrics.csv", index=False)
inst_summary.to_csv("institution_summary_stats.csv", index=False)
