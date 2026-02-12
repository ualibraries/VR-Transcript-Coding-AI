try:
    with open('codebook.json', 'r') as f:
        codebook = json.load(f)
except FileNotFoundError:
    print("Error: The codebook.json file was not found.")
    codebook = {}
except json.JSONDecodeError:
    print("Error: The codebook.json file is not a valid JSON.")
    codebook = {}
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    codebook = {}