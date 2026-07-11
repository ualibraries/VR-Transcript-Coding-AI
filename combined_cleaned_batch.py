import os
import glob
import pandas as pd

# 1. Mount Drive
drive.mount('/content/drive')

# 2. Define the path to your specific folder
# Replace 'YourFolder' with the actual path inside your My Drive
folder_path = '/content/drive/MyDrive/AZ_Only/Cleaned'

# 3. Change the active directory to your folder
os.chdir(folder_path)

# 4. Gather all CSV files in this specific folder
csv_files = glob.glob("*.csv")
csv_files = [f for f in csv_files if f != "master_combined.csv"]

print(f"Found {len(csv_files)} files to combine in {folder_path}.")

# 5. Read each CSV file into a list of DataFrames
all_dataframes = []
for file in csv_files:
    df = pd.read_csv(file)
    
    # Optional but highly recommended: Add a column tracking the source year
    # This extracts the filename (e.g., '2023.csv' becomes '2023')
    year_label = os.path.splitext(file)[0]
    df['Source_Year'] = year_label
    
    all_dataframes.append(df)

# 3. Concatenate all dataframes together vertically
master_df = pd.concat(all_dataframes, ignore_index=True)

# 4. Export the combined data to a new master CSV file
output_file = "master_combined.csv"
master_df.to_csv(output_file, index=False)

print(f"Success! All files combined into '{output_file}'. Total rows: {len(master_df)}")
