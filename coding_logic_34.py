import json
import time
from google import genai
from google.colab import userdata
from preprocessing_util import clean_raw_text, AI_CONFIG, MODEL_NAME

# 1. Initialize API Client Once
api_key = userdata.get('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

# 2. Load Codebook
CODEBOOK_PATH = '/content/drive/MyDrive/34Batch/codebook_theme.json'
with open(CODEBOOK_PATH, 'r') as f:
    CODEBOOK_DICT = json.load(f)

# 3. Centralized Prompting
SYSTEM_PROMPT = f"""
You are an expert qualitative researcher. Code the transcript using the JSON codebook below.
### CODEBOOK:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

VERIFIER_PROMPT = """
You are a Senior Library Auditor. Audit the Coder's output.
LOGIC GATES:
1. REJECT 'Known Item' if the patron is already using the named resource.
2. REJECT 'Library Services' if the librarian is just providing a URL/LibGuide (that is 'Finding Relevant Resources').
3. Ensure exact string matches for codes.

OUTPUT: Return JSON {"is_valid": true/false, "feedback": "reason"}
"""
def code_transcript_with_verify(transcript):
    cleaned_input = clean_raw_text(transcript)
    if len(str(cleaned_input)) < 10:
        return "Abandoned Chat", "N/A", "Insufficient data"

    # --- STEP 1: INITIAL ATTEMPT (Demanding String Format) ---
    initial_prompt = f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}\n\nOUTPUT FORMAT: Provide ONLY the code names separated by ' | '. Do not use JSON."
    res = client.models.generate_content(model=MODEL_NAME, contents=initial_prompt, config=AI_CONFIG)
    
    # Extracting text and thoughts
    initial_code = res.text.strip().replace("```", "").replace("json", "").strip()
    initial_thoughts = getattr(res.candidates[0].content.parts[0], 'thought', "No thoughts recorded")

    # --- STEP 2: SURGICAL VERIFICATION ---
    # We use a very light touch here to avoid the "over-correction" you saw
    v_prompt = f"{VERIFIER_PROMPT}\n\nTRANSCRIPT: {cleaned_input}\n\nPROPOSED CODES: {initial_code}"
    v_res = client.models.generate_content(model=MODEL_NAME, contents=v_prompt)
    
    is_valid = '"is_valid": true' in v_res.text.lower()
    feedback = v_res.text

    # --- STEP 3: REVISION (IF NEEDED) ---
    if not is_valid:
        revision_prompt = f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}\n\nAUDIT FEEDBACK: {feedback}\n\nREVISE AND PROVIDE ONLY THE CODE NAMES SEPARATED BY ' | '."
        rev_res = client.models.generate_content(model=MODEL_NAME, contents=revision_prompt, config=AI_CONFIG)
        final_code = rev_res.text.strip().replace("```", "").replace("json", "").strip()
        return final_code, feedback, f"REVISED | {initial_thoughts}"

    return initial_code, "PASS", initial_thoughts

    return initial_code, "PASS", initial_thoughts
