import os
import pypdf
import chromadb
import time
import sys
from google import genai
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()

# --- J4SON.DEV ROBUST EMBEDDING ENGINE ---
class GeminiEmbeddingFunction:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def name(self):
        return "gemini-embedding-001"

    def __call__(self, input):
        texts = [input] if isinstance(input, str) else input
        max_retries = 5
        retry_delay = 10 
        for attempt in range(max_retries):
            try:
                response = self.client.models.embed_content(
                    model="models/gemini-embedding-001", 
                    contents=texts
                )
                return [[float(v) for v in item.values] for item in response.embeddings]
            except errors.ClientError as e:
                if "429" in str(e):
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e
        return []

    def embed_query(self, input):
        return self.__call__(input)

    def embed_documents(self, input):
        return self.__call__(input)

def run_ingestion():
    print("--- J4SON.DEV: Knowledge Ingestion Engine ---")
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_ef = GeminiEmbeddingFunction(api_key=api_key)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "economics_db")
    db = chromadb.PersistentClient(path=db_path)

    collection = db.get_or_create_collection(
        name="economics_textbook", 
        embedding_function=gemini_ef
    )

    pdf_path = "Alvl Eco.pdf"
    reader = pypdf.PdfReader(pdf_path)
    all_docs, all_metas, all_ids = [], [], []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            all_docs.append(text)
            all_metas.append({"page": i + 1})
            all_ids.append(f"page_{i + 1}")

    existing_ids = set(collection.get(include=[])['ids'])
    batch_size = 10 
    for i in range(0, len(all_docs), batch_size):
        end_idx = min(i + batch_size, len(all_docs))
        batch_ids = all_ids[i:end_idx]
        if not all(bid in existing_ids for bid in batch_ids):
            collection.add(
                documents=all_docs[i:end_idx],
                metadatas=all_metas[i:end_idx],
                ids=batch_ids
            )
            print(f"✅ Processed Page {end_idx}...")
            time.sleep(5) 

    print(f"\n🚀 SUCCESS: Knowledge Base Fully Synced.")

if __name__ == "__main__":
    run_ingestion()