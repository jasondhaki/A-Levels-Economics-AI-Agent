import os
import sys
import warnings

# --- 1. CLOUD SQLITE FIX (Must be at the very top) ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types
import chromadb
import time
from google.genai import errors
from dotenv import load_dotenv

# Initialize Environment
load_dotenv()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

# --- 2. J4SON.DEV ROBUST EMBEDDING ENGINE ---
class GeminiEmbeddingFunction:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def name(self):
        return "gemini-embedding-001"

    def __call__(self, input):
        # Universal handler: ensures input is a list of strings
        texts = [input] if isinstance(input, str) else input
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.embed_content(
                    model="models/gemini-embedding-001", 
                    contents=texts
                )
                # CRITICAL: Always return a List of Lists [[float, float, ...]]
                # This satisfies the Rust engine's 'Sequence' requirement
                return [[float(v) for v in item.values] for item in response.embeddings]
            except errors.ClientError as e:
                if "429" in str(e):
                    time.sleep(2)
                else:
                    raise e
        return []

    # REQUIRED by ChromaDB search logic
    def embed_query(self, input):
        return self.__call__(input)

    # REQUIRED by ChromaDB ingestion logic
    def embed_documents(self, input):
        return self.__call__(input)

# --- 3. CONFIGURATION & DATABASE ---
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
gemini_ef = GeminiEmbeddingFunction(api_key=api_key)

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "economics_db")

db = chromadb.PersistentClient(path=db_path)
collection = db.get_or_create_collection(
    name="economics_textbook",
    embedding_function=gemini_ef
)

# --- 4. AGENT ARCHITECTURE ---
class AgentState(TypedDict):
    question: str
    context: str
    answer: str
    iterations: int

def retrieve_node(state: AgentState):
    print("--- J4SON.DEV ENGINE: ACCESSING CORE KNOWLEDGE ---")
    query = state["question"]
    
    # query_texts=[query] triggers the .embed_query method
    results = collection.query(query_texts=[query], n_results=3)
    
    context_parts = []
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            text = results['documents'][0][i]
            page = results['metadatas'][0][i].get('page', 'Unknown')
            context_parts.append(f"Source Page {page}: {text}")
    
    return {"context": "\n\n".join(context_parts), "iterations": state.get("iterations", 0) + 1}

def grade_node(state: AgentState):
    print("--- J4SON.DEV ENGINE: GRADING RETRIEVAL ---")
    keywords = ["scarcity", "choice", "demand", "supply", "economic", "market", "price", "need", "want", "elasticity", "gdp", "hdi"]
    context_lower = state["context"].lower()
    return "professor" if any(word in context_lower for word in keywords) else "refusal"

def draft_node(state: AgentState):
    print("--- J4SON.DEV ENGINE: FORMULATING ECONOMIC RESPONSE ---")
    system_prompt = f"""
    You are the J4SON.DEV Economics Expert.
    Cite Page Numbers for the theories used.
    CONTEXT: {state['context']}
    """
    response = client.models.generate_content(
        model="models/gemini-3.1-flash-lite",
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.3),
        contents=[state["question"]]
    )
    return {"answer": response.text}

def refusal_node(state: AgentState):
    return {"answer": "I don't have enough specific information in my knowledge base to answer this query accurately."}

def critique_node(state: AgentState):
    return {"iterations": state["iterations"]}

# --- 5. BUILD THE GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("researcher", retrieve_node)
workflow.add_node("professor", draft_node)
workflow.add_node("refusal", refusal_node)
workflow.add_node("critic", critique_node)
workflow.set_entry_point("researcher")
workflow.add_conditional_edges("researcher", grade_node, {"professor": "professor", "refusal": "refusal"})
workflow.add_edge("professor", "critic")
workflow.add_edge("critic", END)
workflow.add_edge("refusal", END)
app = workflow.compile()

if __name__ == "__main__":
    user_query = input("Ask an Economics question: ")
    for output in app.stream({"question": user_query, "iterations": 0}):
        for key, value in output.items():
            if "answer" in value: print("\nFINAL ANSWER:\n", value["answer"])