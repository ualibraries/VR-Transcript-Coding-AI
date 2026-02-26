# Proposed addition to main loop for the A/B Test
MODELS_TO_TEST = ["gemini-2.5-flash-lite", "gemini-3-flash"]

for i, row in df.sample(100).iterrows():
    results = {}
    for model_ver in MODELS_TO_TEST:
        # Pass the model_ver dynamically to your code_transcript function
        results[model_ver] = code_transcript(row['Transcript'], model_ver)
    
    # Log results to a comparison CSV
    save_comparison(row['ID'], results)
