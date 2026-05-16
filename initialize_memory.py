import json
import chromadb
from chromadb.utils import embedding_functions

# Configuration
INPUT_FILE = 'Economics_Chunks.json'
DB_PATH = './economics_db'

def initialize_vector_db():
    print("🧠 Initializing the j4son.dev Vector Memory...")
    
    # 1. Set up the local ChromaDB client
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 2. Use a high-quality, free embedding model (Sentence Transformers)
    # This will download the model (~400MB) on the first run
    embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 3. Create (or get) the collection
    collection = client.get_or_create_collection(
        name="economics_textbook",
        embedding_function=embedding_model
    )
    
    # 4. Load your chunks
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"📥 Loading {len(chunks)} chunks into memory. This may take a moment...")
    
    # 5. Add chunks to the DB
    # We batch them to avoid memory spikes
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        
        collection.add(
            ids=[f"id_{j}" for j in range(i, i + len(batch))],
            documents=[item["text"] for item in batch],
            metadatas=[item["metadata"] for item in batch]
        )
        print(f"✅ Indexed {i + len(batch)} / {len(chunks)} chunks...")

    print(f"\n✨ Success! Vector Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    initialize_vector_db()