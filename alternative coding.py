# --- 2. THE SYSTEM PROMPT (V3.3.3 Forensic Update) ---
SYSTEM_PROMPT = f"""
### ROLE
You are a Forensic Data Auditor. You do not summarize "Main Points"; you perform an EXHAUSTIVE CENSUS of all entities, actions, and services mentioned.

### THE AUDIT PROTOCOL: "OBJECT + ACTION"
For every transcript, you must identify both the Object (The Thing) and the Action (The Request).
1. Identify Objects: Laptops, Specific Book Titles, Passwords, Course Codes, Study Rooms.
2. Identify Actions: Renewing, Troubleshooting, Searching, Asking for Hours.
3. Check the Origin: 
   - Patron mentions Title -> 'Known Item'
   - Librarian mentions Title -> 'Finding Relevant Resources' (NOT Known Item)

### THE ENTITY MANDATE (ZERO TOLERANCE)
• Borrow Tech: MANDATORY if hardware is mentioned (Laptops, Tripods, etc.) regardless of the intent (returning, hours, or damage).
• Known Item: MANDATORY if Patron provides specific title/author first. Apply even if the issue is a technical/link error.
• Connectivity vs. Account: Code BOTH if they mention a login failure AND their account status.
• Topic/Genre: "Poetry," "History," or "3 articles" is 'Finding Relevant Resources'.

### MANDATORY REASONING FORMAT
You MUST use this checklist format:
1. Patron Entity: [Noun/None] -> [Code]
2. Action/Intent: [Verb/Request] -> [Code]
3. Origin Check: [Who provided info?] -> [Decision]
4. Exclusion Check: [Why was a similar code omitted?]

# CODEBOOK JSON:
{json.dumps(CODEBOOK_DICT, indent=2)}
"""

# --- 3. CORE FUNCTIONS (With AI Coffee Injection) ---
def code_transcript(transcript):
    cleaned_input = clean_raw_text(transcript)
    
    if len(cleaned_input) < 10:
        return "Abandoned Chat | Insufficient data"

    # THE AI COFFEE: This reminder is injected into every single API call
    # to prevent the "Analytical Fatigue" seen at Item 90.
    coffee_reminder = (
        "\n\n### FRESHNESS REMINDER:\n"
        "Do not drift. If the patron named a specific book, you MUST code 'Known Item'. "
        "If they mentioned a laptop, you MUST code 'Borrow Tech'. "
        "Capture EVERY intent, even if the primary issue is a technical error."
    )

    last_error = "Unknown Error"

    for attempt in range(3): 
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                # We combine the System Prompt, the Specific Transcript, and the Coffee Reminder
                contents=f"{SYSTEM_PROMPT}\n\nTranscript: {cleaned_input}\n{coffee_reminder}",
                config=AI_CONFIG 
            )
            
            return response.text.replace("**", "").replace("\n", " ").strip()
            
        except Exception as e:
            # ... [Existing Error Handling Logic] ...
