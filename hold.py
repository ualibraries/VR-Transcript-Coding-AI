def code_transcript(transcript, feedback=None): # <--- Added feedback=None here
    """Orchestrates API call with March 2026 Thinking extraction and feedback loop."""
    cleaned_input = clean_raw_text(transcript)
    if len(str(cleaned_input)) < 10:
        return "Abandoned Chat | Insufficient data", ""

    coffee_reminder = "\n\n### PRECISION CHECK: Identify all distinct categories. Do not drift."
    
    # NEW: Construct the instruction block if feedback is provided
    audit_intervention = ""
    if feedback:
        audit_intervention = f"\n\n### CRITICAL RE-CODING TASK:\nYour previous output was REJECTED by the auditor for the following reason:\n{feedback}\n\nPlease correct your logic and re-map the codes accordingly."

    last_error = "Unknown Error"

    for attempt in range(3):
        try:
            # Inject the audit_intervention between the prompt and the transcript
            full_prompt = f"{SYSTEM_PROMPT}{audit_intervention}\n\nTranscript: {cleaned_input}{coffee_reminder}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=full_prompt, # <--- Uses the new combined prompt
                config=AI_CONFIG
            )

            thoughts = []
            final_answer_parts = []

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought:
                        thoughts.append(part.thought) # Use .thought attribute for 2026 models
                    elif hasattr(part, 'text') and part.text:
                        final_answer_parts.append(part.text)

            clean_code = " ".join(final_answer_parts).replace("**", "").replace("\n", " ").strip()
            mental_process = " ".join(thoughts).replace("\n", " ").strip()

            # Fallback if thoughts were embedded in text
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
