import pandas as pd
import re
from datetime import datetime

def analyze_ua_conversation(transcript_text):
    # 1. Define the regex pattern for UA transcripts: [Time] - [Speaker] : [Text]
    # This captures the Time, Speaker, and Message
    pattern = r"(\d{2}:\d{2}:\d{2}) - (.*?) : (.*?)(?=\n\d{2}:\d{2}:\d{2} - |$)"
    
    turns = []
    matches = re.findall(pattern, transcript_text, re.DOTALL)
    
    for match in matches:
        timestamp_str, speaker, text = match
        turns.append({
            'timestamp': datetime.strptime(timestamp_str, '%H:%M:%S'),
            'speaker': 'Librarian' if 'UA' in speaker else 'Patron',
            'text': text.strip(),
            'word_count': len(text.split())
        })
    
    df = pd.DataFrame(turns)
    
    if df.empty:
        return "No turns detected. Check transcript format."

    # --- CALCULATIONS ---
    
    # A. Latency (Response Time) - Time difference between turns
    df['latency'] = df['timestamp'].diff().dt.total_seconds()
    
    # B. Speaker Dominance (Word Count)
    total_words = df['word_count'].sum()
    lib_words = df[df['speaker'] == 'Librarian']['word_count'].sum()
    patron_words = df[df['speaker'] == 'Patron']['word_count'].sum()
    
    # C. Turn Counts
    lib_turns = len(df[df['speaker'] == 'Librarian'])
    patron_turns = len(df[df['speaker'] == 'Patron'])
    
    # D. "Friction" - Average time the patron waits for a librarian response
    avg_wait_time = df[df['speaker'] == 'Librarian']['latency'].mean()

    # --- RESULTS ---
    metrics = {
        'Total Turns': len(df),
        'Turn Ratio (Lib:Patron)': f"{lib_turns}:{patron_turns}",
        'Librarian Word %': f"{(lib_words/total_words)*100:.1f}%",
        'Avg Patron Wait (sec)': f"{avg_wait_time:.1f}s",
        'Max Latency': f"{df['latency'].max()}s"
    }
    
    return metrics, df

# --- TEST WITH YOUR UA EXAMPLE ---
ua_sample = """17:18:38 - UA : Hi - this is UA. <br />
17:18:46 - [REDACTED NAME] : Hi, I'm [REDACTED]
17:19:43 - [REDACTED NAME] : My professor applied proxy card last week, but I didn't get any information after then.
17:20:01 - UA : Is this a computer related issue?<br />
17:20:44 - [REDACTED NAME] : No, I'm wondering when I can get the card so I can pick up her books.
17:20:56 - UA : Oh, gotcha. <br />
17:21:20 - UA : Let me make a ticket out of this chat and someone will get back to you via email.<br />
17:22:12 - [REDACTED NAME] : Thank you.
17:22:39 - UA : You're welcome, take care.<br />
17:22:51 - [REDACTED NAME] : take care."""

stats, detailed_df = analyze_ua_conversation(ua_sample)

print("--- UA SERVICE RHYTHM REPORT ---")
for key, value in stats.items():
    print(f"{key}: {value}")
