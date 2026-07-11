import pandas as pd

# 1. Load the large CSV file
df = pd.read_csv("your_file.csv")

# 2. Define the desired column order (New_AI_Final_Code is omitted)
desired_columns = [
    "StudyID",
    "Transcript",
    "Timestamp",
    "Referrer",
    "Wait Time (seconds)",
    "Duration (seconds)",
    "AI_Final_Code",
    "AI_Reasoning",
    "Processed_At",
    "AI_Thoughts",
    "Source_Year"
]

# 3. Reorder and drop the unwanted column
df_reordered = df[desired_columns]

# 4. Save the processed data to a new CSV file
df_reordered.to_csv("reordered_file.csv", index=False)
