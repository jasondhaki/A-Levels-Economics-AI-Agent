from google import genai

# Use your validated API Key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- j4son.dev Model Discovery ---")
try:
    # Listing models with the correct 2026 attribute 'supported_actions'
    for model in client.models.list():
        print(f"ID: {model.name}")
        print(f"   Actions: {model.supported_actions}")
        print("-" * 30)
except Exception as e:
    print(f"Error listing models: {e}")