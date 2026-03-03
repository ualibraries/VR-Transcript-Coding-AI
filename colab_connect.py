from google import genai
from google.colab import userdata # Use this to grab the secret correctly
from google.genai import types

# 1. Explicitly pull the key from Colab Secrets
# Make sure the name matches EXACTLY what you typed in the 'lock' icon
key = userdata.get('GEMINI') 

# 2. Initialize the client WITH the key and Vertex=False
client = genai.Client(
    api_key=key,
    vertexai=False 
)

# 3. Use the stable 2026 model ID
MODEL_ID = "gemini-3.1-flash-preview" 

print("✅ Client re-initialized with explicit authentication.")
