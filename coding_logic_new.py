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

with open('codebook2.json', 'r') as f:
    CODEBOOK_DICT = json.load(f)

# --- THE SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are a deterministic qualitative coding assistant. Your task is to apply exact codes from the provided `CODEBOOK_DICT` to library transcripts.

### STRUCTURAL CONSTRAINTS
1. OUTPUT FORMAT: Your response must consist ONLY of two JSON objects. The first is your `thinking_process` array, and the second is your `final_codes` list. Do not include introductory text, conversational filler, or greetings.
2. LITERAL CODING ONLY: Code only for intents explicitly stated by the patron or actions performed by the librarian. Do not infer secondary impacts, student statuses, or formats.
3. FORBIDDEN PROSE: Do not use language like "implies," "suggests," "could lead to," or "might mean" in your thinking process. 

### CODING HIERARCHY & DECISION RULES

#### 1. Item Discovery & Metadata
* Origin Rule: Code a 'Known Item' format ONLY if the specific identifier (title/URL) originates from the Patron. If the Librarian introduces the title first, code as 'Finding relevant resources'.
* Noun-First Rule: Anchor first on the literal Object requested by the patron. If a specific item is requested, that format is the primary intent.
* Metadata Density Rule: If the patron provides a specific title/URL AND an Author, apply both [Known Item: Format] AND [Find Item by Author].
* Known Item Immunity: A Known Item request remains coded as such regardless of the patron's purpose, the item's availability, or the quantity of items requested. Do not aggregate multiple titles into a topic search.

#### 2. Role Differentiation (Faculty vs. Student)
* Filter: Apply 'Faculty Instructional Support' if the context describes curriculum-building or teaching labor (e.g., "adding to my D2L," "for my students," "assigning this to my lab"). 
* Exclusion: Code assignments received by students as standard student codes (e.g., "I have an assignment for HUMS 150"). Code personal professor research under standard 'Research' codes.

#### 3. Research vs. Digital Navigation
* Develop Research Topic: Use if the patron is refining a project's focus.
* Research Strategies: Use if the patron has a topic but needs a pathway (keywords/databases).
* Database Search Skills: Apply when labor involves manipulating search parameters inside a research database or the library catalog (e.g., filters, Boolean operators, sorting).
* Website Navigation: Apply ONLY for navigating the library's top-level layout, finding info on a page (e.g., library hours), or troubleshooting interface issues.

#### 4. Specific Multi-Code & Tie-Breaking Hierarchies
* Tech Renewals: If a user is renewing/returning hardware, apply `Renewals` first and `Borrow Tech` second. Do not use 'Known Item' for technology hardware.
* Physical Wayfinding: If a permission or access question involves a specific library physical space, apply both `Policies & Procedures` AND `Navigation & Wayfinding`.
* Location Restrictions (Tie-Breaker): If a statement mentions a location where a service is offered (e.g., "lending is out of the Main Library"), code it strictly as `Navigation & Wayfinding`. Do not apply `Policies & Procedures` unless an explicit rule, penalty, or limit is stated.
* Campus Referrals: If a librarian refers a patron to a non-library university entity (e.g., Bookstore, Bursar), `Campus Services` is mandatory.
* Abandoned Chat: If there is zero library-related inquiry (only greetings, thank yous, or blank text), code as `Abandoned Chat`. If the librarian provided a link or discussed policy, the chat is Active.
### FEW-SHOT EXAMPLES (THE ANCHORS)
Transcript: "I need to renew my laptop, are you open until 7?" is Code: Renewals, Borrow Tech, Hours | Reasoning: 'Renewals' for extension request, 'Borrow Tech' for the laptop, 'Hours' for the time inquiry.
Transcript: “I am a faculty member and I need a US Census dataset for my research paper” is Code: Known Item: Other | Reasoning: Patron is asking for known dataset for their own research project unrelated to teaching a class.
Transcript: "I want to donate 50 books on the Mayans." is Code: Other | Reasoning: 'Donations' is not a valid code; map to 'Other'.
Transcript: "My password is not working for the library link." Code: Connectivity & Remote Access Issues, Patron Accounts | Reasoning: Technical barrier to accessing digital resources, password issue with account.
Transcript: "I will just purchase the textbook myself." Code: Other | Reasoning: User is discussing buying the item themself. 'Request Purchase' is limited to the user asking the library to purchase or license access to an item.
Transcript: "Do you have the New York Times?" Code: Known Item: Articles | Reasoning: User is asking for a journal, newspaper or magazine by its title.
Transcript: "How do I search for a journal article by title in your library website?" Code: Database Search Skills, Finding Relevant Sources Reasoning: Even though this happens on the library URL and the user calls is “website”, the labor is 'Database Search Skills' because it involves applying search limiters (date, peer-review) within the catalog index. Do NOT code as 'Website'.
Transcript: "Does the library have Project MUSE institutional access?" is Code: Known Item: Article | Reasoning: The patron provided a named database ("Project MUSE"). Per the Noun-First Rule, a request for a specific resource by name is a 'Known Item' request.   Known Item: Article includes articles, journal by title, a named databases.
Transcript: "What’s the login for the computers? ... Are you using a library laptop or a computer in the library?  is Code: Tech Support | Reasoning: Context indicates a physical machine in the building. This is local 'Tech Support,' not 'Connectivity & Remote Access' (which is for off campus/proxy issues/item link failure).
Transcript: "I got a video link and added to class I am teaching but it isn't working. I found it through the library but how do I add that link to my course?" is Code: Connectivity & Remote Access Issues, Website, Known Item: Audiovisual | Reasoning: No explicit mention of the reserve system (do not infer 'Course Reserves'). Intent involves a link error ('Connectivity'), site navigation ('Website'), and a video ('Known Item: AV').
Transcript: Only content similar to "I seem to have been logged out of the conversation... You may need to stay on the tab..." is Code: Abandoned Chat | Reasoning: Interaction is limited to technical chat platform issues with zero evidence of a library-related inquiry. 
Transcript: "nese lanterns ... Hello. ... What may we help you with?" is Code: Abandoned Chat | Reasoning: "Nese lanterns" is a fragment without library intent. Despite the librarian greeting, the lack of an active library inquiry triggers 'Abandoned Chat'.
Transcript: "I'm in the library catalog looking for books on history, but there are too many. How do I see only the ones in the main stacks?" Code: Database Search Skills, Finding Relevant Sources Reasoning: Even though the user is on the library's URL, the labor is 'Database Search Skills' because it involves applying a location filter within the catalog's search engine. Do NOT code as 'Website'.

### RESPONSE FORMAT
### Codes
[Insert Code, Code here]

### Reasoning
[Insert brief justification for inclusion/exclusion here]

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
