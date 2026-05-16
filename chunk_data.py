import re
import json

# Configuration
INPUT_FILE = 'Economics_Structured_Data.md'
OUTPUT_FILE = 'Economics_Chunks.json'
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 100 # To keep context between chunks

def semantic_chunking():
    print("✂️ Starting the j4son.dev Semantic Chunker...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by the Page markers we created in Step 1
    pages = re.split(r'## Page (\d+)', content)
    
    chunks_with_metadata = []
    
    # re.split creates a list: ['', '1', 'page 1 text', '2', 'page 2 text'...]
    for i in range(1, len(pages), 2):
        page_num = pages[i]
        page_text = pages[i+1].strip()
        
        # Split the page text into smaller chunks
        for j in range(0, len(page_text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_text = page_text[j : j + CHUNK_SIZE]
            
            chunks_with_metadata.append({
                "text": chunk_text,
                "metadata": {
                    "page": page_num,
                    "source": "A-Level Economics Book"
                }
            })

    # Save to a JSON file for the next step
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks_with_metadata, f, indent=4)

    print(f"✅ Success! Created {len(chunks_with_metadata)} chunks with page metadata.")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    semantic_chunking()