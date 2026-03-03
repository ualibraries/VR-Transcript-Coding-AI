from google import genai
from google.genai import types
from google.colab import userdata

# 1. Initialize with the Beta endpoint for maximum visibility
client = genai.Client(
    api_key=userdata.get('GEMINI_API_KEY'),
    vertexai=False,
    http_options=types.HttpOptions(api_version='v1beta')
)

print("🔍 CURRENT LIVE MODELS (Tucson Time: March 3, 2026)\n")
print("-" * 50)

try:
    # In the GA SDK, we just iterate directly through the list
    for m in client.models.list():
        # Clean up the string for your config file
        model_id = m.name.replace("models/", "")
        
        # We'll use a simple print to see everything available
        print(f"✅ {model_id}")

except Exception as e:
    print(f"❌ Error fetching list: {e}")

print("-" * 50)
print("💡 COPY THE EXACT NAME ABOVE INTO YOUR preprocessing_util.py")
