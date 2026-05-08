import json
import os
import time
import pandas as pd
from google import genai
from google.genai import types
from google.colab import userdata

# mean librarian script
# --- INITIALIZATION ---
client = genai.Client(
    api_key=userdata.get('GEMINI_API_KEY'),
    # This correctly forces the SDK to use the Developer branch (not Vertex)
    vertexai=False,
    # This ensures you're hitting the Beta endpoint for the latest 3.1 features
    http_options=types.HttpOptions(api_version='v1beta')
)



VERIFIER_SYSTEM_PROMPT = """
You are a Senior Library Assessment Auditor. Your role is to conduct a "Glass Box" audit of a Coder Agent's work.
You are skeptical and demand high evidence. You must enforce the following strictly:

LOGIC GATES:
1. THE 'KNOWN ITEM' GATE: If a patron names a resource (e.g., 'Web of Science') but says they are already using it, REJECT any 'Known Item' code. Assistance in an active session is 'Database Search Skills'.
2. THE 'RESOURCE VS SERVICE' GATE: If the librarian provides a URL, a LibGuide link, or a database name, this is a RESOURCE. Reject 'Library Services' (which is for professional acts like ILL or policy). Provide 'Finding Relevant Resources' instead.
3. THE 'EXACT STRING' GATE: Ensure codes match the Codebook exactly. No lowercase or paraphrased codes (e.g., 'Faculty instruction' is WRONG; 'Faculty Instructional Support' is RIGHT).

OUTPUT FORMAT:
Return a JSON object:
{
  "is_valid": true/false,
  "feedback": "If false, explain exactly which gate was violated and why."
}
"""

def verify_coding(transcript_text, coder_output):
    prompt = f"""
    TRANSCRIPT: 
    {transcript_text}

    CODER'S PROPOSED CODES AND REASONING:
    {coder_output}

    Perform the audit. Does this follow all Logic Gates?
    """
    
    response = model.generate_content([VERIFIER_SYSTEM_PROMPT, prompt])
    
    # Simple logic to parse the JSON output (you can add a real JSON parser here)
    if '"is_valid": true' in response.text:
        return True, "PASS"
    else:
        # Extract the feedback string
        return False, response.text
