import json
import os
import time
import pandas as pd
from google import genai
from google.genai import types
from google.colab import userdata
from preprocessing_util import clean_raw_text, AI_CONFIG, MODEL_NAME

# --- INITIALIZATION ---
client = genai.Client(
    api_key=userdata.get('GEMINI_API_KEY'),
    vertexai=False,
    http_options=types.HttpOptions(api_version='v1beta')
)

# Load codebook for the prompt
with open('codebook2.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

# --- THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
### NEGATIVE CONSTRAINTS (THE "NO-GO" ZONE)
• NO INVENTED CODES: Use ONLY the exact wording of the code keys as provided in the JSON Codebook (CODEBOOK_DICT). Do not summarize or combine code names.
• NO INFERENTIAL CODING: Literal Evidence Only. You MUST only apply codes for intents explicitly stated by the patron or services performed by the librarian.
• Prohibited Language: In your reasoning, you are strictly forbidden from using words like "implies," "suggests," "could lead to," or "might mean."
• DO NOT INFER FORMATS: Example - Music Scores = 'Known Item: Other'. Never 'Known Item: AV'
• DO NOT INFER COURSE RESERVES: Do not assume 'Course Reserves' solely because their need mentions a class or course.
• DO NOT INFER ADDITIONAL IMPACTS: (e.g., HVAC issues do not mean 'Noise Issues').

### CORE LOGIC
• Keyword Contextualization: Map keywords to "Intent" and "Definition" sections. 
• Multi-Labeling: Assign all relevant codes. Separate with commas.
• Origin-Based Coding: A Known Item code (Book, Article, AV) can ONLY be triggered if unique item details originate from the Patron.
• Metadate Density Rule: If the patron provides a unique identifier + Author, apply both [Known Item: Format] AND [Find Item by Author].
• Research Spectrum: Distinguish between 'Develop Research Topic' (refining idea), 'Research Strategies' (need pathway/databases), and 'Database Search Skills' (mechanical tool use).
• Physical Wayfinding: If a permission question involves a specific library space, apply both 'Policies & Procedures' and 'Navigation & Wayfinding'.

### FEW-SHOT EXAMPLES (THE ANCHORS)
Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Tech, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
Transcript: "I am a faculty member and I need a US Census dataset for my research paper" is Code: Known Item: Other | Reasoning: Patron is asking for known dataset for their own research project unrelated to teaching a class.
Transcript: "Do you have the New York Times?" Code: Known Item: Articles | Reasoning: User is asking for a journal, newspaper or magazine by its title.

### RESPONSE FORMAT
Code, Code | [Reasoning: Brief justification for inclusion/exclusion]

### CODEBOOK JSON:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

def code_transcript(transcript):
    """Orchestrates API call with March 2026 Thinking extraction."""
    cleaned_input = clean_raw_text(transcript)
    if len(str(cleaned_input)) < 10:
        return "Abandoned Chat | Insufficient data", ""

    coffee_reminder = "\n\n### PRECISION CHECK: Identify all distinct categories. Do not drift."
    last_error = "Unknown Error"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}{coffee_reminder}",
                config=AI_CONFIG
            )

            thoughts = []
            final_answer_parts = []

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought:
                        thoughts.append(part.text)
                    elif hasattr(part, 'text') and part.text:
                        final_answer_parts.append(part.text)

            clean_code = " ".join(final_answer_parts).replace("**", "").replace("\n", " ").strip()
            mental_process = " ".join(thoughts).replace("\n", " ").strip()

            # Fallback if thoughts were embedded in text (v1beta quirk)
            if not mental_process and "THOUGHT:" in clean_code:
                parts = clean_code.split("THOUGHT:", 1)
                clean_code = parts[0].strip()
                mental_process = parts[1].strip() if len(parts) > 1 else ""

            return clean_code, mental_process

        except Exception as e:
            last_error = str(e)
            if any(err in last_error for err in ["503", "429"]):
                wait = (attempt + 1) * 10
                time.sleep(wait)
            else:
                time.sleep(5)
                
    return f"ERROR | {last_error[:50]}", ""

# Note: The main() function and batch logic have been moved to the Orchestrator script (run_34k_audit.py)
