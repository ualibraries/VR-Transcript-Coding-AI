import shutil
import os

# Define the source path (where your file is currently saved in the Colab VM)
source_file_path = '/content/coded_results_Round20.csv' # Replace with your actual file path

# Define the destination path (a specific folder in your Google Drive)
# Ensure the folder exists in your Google Drive (e.g., a folder named 'Colab_Outputs')
destination_folder_path = '/content/drive/MyDrive/Colab_Outputs/'

# Ensure the destination folder exists (optional but recommended)
os.makedirs(destination_folder_path, exist_ok=True)

# Move the file to the destination folder
# The destination should include the file name in the new location
destination_file_path = os.path.join(destination_folder_path, os.path.basename(source_file_path))
shutil.move(source_file_path, destination_file_path)

print(f'File moved from {source_file_path} to {destination_file_path}')
