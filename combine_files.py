import pandas as pd
import glob
import os

# 1. Define the path where your CSV files are located
path = '/content/drive/MyDrive/34Batch/Cleaned/' # Update this to your folder path

# 2. Use glob to find all files ending in .csv
all_files = glob.glob(os.path.join(path, "*.csv"))

# 3. Read each CSV and drop any column that doesn't have a name
def read_and_clean(file):
    df = pd.read_csv(file)
    # This drops any column where the header starts with "Unnamed"
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

dataframes = [read_and_clean(file) for file in all_files]

# 4. Concatenate all DataFrames into one master DataFrame
# ignore_index=True resets the row numbers so they are sequential
master_df = pd.concat(dataframes, ignore_index=True)

# 5. Output the combined data to a new master CSV file
master_df.to_csv("/content/drive/MyDrive/34Batch/Theme/master_output_test.csv", index=False)

print(f"Successfully merged {len(all_files)} files into 'master_output_test.csv'.")
