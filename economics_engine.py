import os
import warnings
import time

# 1. Professional j4son.dev Console Cleanup
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message="You are sending unauthenticated requests to the HF Hub")

from google import genai
from google.genai import types
import chromadb

# 2. Setup the Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 3. Connect to Local Memory
db = chromadb.PersistentClient(path="./economics_db")
collection = db.get_collection(name="economics_textbook")

def query_economics_ai(user_query):
    # Retrieve relevant chunks
    results = collection.query(query_texts=[user_query], n_results=3)
    
    context_parts = []
    for i in range(len(results['documents'][0])):
        text = results['documents'][0][i]
        page = results['metadatas'][0][i].get('page', 'Unknown')
        context_parts.append(f"--- SOURCE: Page {page} ---\n{text}")
    
    context_text = "\n\n".join(context_parts)
    
    # Define Persona and Grounding Rules
    system_prompt = f"""
    You are the j4son.dev Economics Expert AI (Powered by Gemini 3.1).
    Your goal is to answer A-level Economics questions strictly using the provided context.
    
    RULES:
    1. ONLY use the provided context from the textbook.
    2. If the answer is not in the context, strictly say: "I don't know based on the provided Economics text."
    3. Always cite the specific Page Number from the context header.
    4. Use professional economic terminology.
    
    CONTEXT FROM TEXTBOOK:
    {context_text}
    """

    # Using the quota-optimized Gemini 3.1 Flash Lite
    response = client.models.generate_content(
        model="models/gemini-3.1-flash-lite", 
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1 
        ),
        contents=[user_query]
    )
    
    return response.text

if __name__ == "__main__":
    print("--- j4son.dev Economics Engine (Gemini 3.1 Lite) Online ---")
    query = input("Ask an Economics question: ")
    print("\n" + query_economics_ai(query))