from google import genai
import os

# DO NOT use the Colab Secret for this test. Paste the raw key.
MY_KEY = "AIzaSyDq6Stz4eD4qY0_S9cPDomkimHrWvRvrC8" 

client = genai.Client(
    api_key=MY_KEY,
    vertexai=False # Forces Developer Mode
)

try:
    # Use the specific March 2026 model ID
    response = client.models.generate_content(
        model='gemini-2.0-flash', # Testing a 2.0 model first as it's the most stable
        contents="Hello"
    )
    print("✅ AUTHENTICATION RECOVERED!")
except Exception as e:
    print(f"❌ STILL FAILING. Logic check: {e}")
