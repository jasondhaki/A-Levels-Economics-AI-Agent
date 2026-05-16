# --- CLOUD SQLITE FIX (MUST BE AT THE VERY TOP) ---
try:
    __import__('pysqlite3')
    import sys
    import os
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import warnings
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types
import chromadb
from dotenv import load_dotenv

load_dotenv()

# 1. Professional J4SON.DEV Console Cleanup
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message="You are sending unauthenticated requests to the HF Hub")

# 2. Configuration & Pathing
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Use absolute pathing for Streamlit Cloud stability
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "economics_db")

db = chromadb.PersistentClient(path=db_path)

# Safe retrieval: Use get_or_create to prevent "Collection Not Found" errors
collection = db.get_or_create_collection(name="economics_textbook")

class AgentState(TypedDict):
    question: str
    context: str
    answer: str
    iterations: int

# --- NODE 1: The Researcher ---
def retrieve_node(state: AgentState):
    print("--- THINKING: Searching Textbook Database ---")
    query = state["question"]
    results = collection.query(query_texts=[query], n_results=3)
    
    context_parts = []
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            text = results['documents'][0][i]
            page = results['metadatas'][0][i].get('page', 'Unknown')
            context_parts.append(f"Source Page {page}: {text}")
    
    return {"context": "\n\n".join(context_parts), "iterations": state.get("iterations", 0) + 1}

# --- NODE 2: The Gatekeeper (Grader) ---
def grade_node(state: AgentState):
    print("--- THINKING: Grading Retrieval Relevance ---")
    keywords = ["scarcity", "choice", "demand", "supply", "economic", "market", "price", "need", "want", "elasticity", "gdp", "hdi"]
    context_lower = state["context"].lower()
    
    if any(word in context_lower for word in keywords) and len(state["context"]) > 100:
        return "professor"
    else:
        return "refusal"

# --- NODE 3: The Professor (The Contextual Strategist) ---
def draft_node(state: AgentState):
    print("--- THINKING: Solving Scenario-Based Problem ---")
    
    system_prompt = f"""
    You are the J4SON.DEV Economics Expert.
    You specialize in applying economic theory to specific real-world or hypothetical scenarios.
    
    RULES:
    1. If the question describes a specific event or policy (a 'scenario'), identify the key stakeholders involved.
    2. Explain the immediate (short-run) and long-term impacts on these stakeholders.
    3. Use a 'Cause and Effect' structure to show how the policy/event ripples through the market.
    4. Cite Page Numbers for the theories used to justify your predictions.
    
    CONTEXT:
    {state['context']}
    """
    
    response = client.models.generate_content(
        model="models/gemini-3.1-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3 
        ),
        contents=[state["question"]]
    )
    return {"answer": response.text}

# --- NODE 4: The Refusal Node ---
def refusal_node(state: AgentState):
    print("--- THINKING: Handling Missing Information ---")
    return {"answer": "I am sorry, but I don't have enough information in my restricted knowledge base to answer this query accurately."}

# --- NODE 5: The Critic (Self-Correction) ---
def critique_node(state: AgentState):
    print("--- THINKING: Critiquing Answer for Accuracy ---")
    
    system_prompt = """
    You are a strict A-level Economics Examiner. 
    Review the provided answer for:
    1. Does it have Page Number citations?
    2. Is the economic logic sound?
    3. Is it strictly based on the context?

    If the answer is perfect, respond with 'PASS'.
    If it needs improvement, respond with the specific error.
    """
    
    response = client.models.generate_content(
        model="models/gemini-3.1-flash-lite",
        config=types.GenerateContentConfig(system_instruction=system_prompt),
        contents=[f"Critique this answer: {state['answer']}"]
    )
    
    print(f"CRITIQUE RESULT: {response.text}")
    return {"iterations": state["iterations"]}

# --- BUILD THE GRAPH ---
workflow = StateGraph(AgentState)

workflow.add_node("researcher", retrieve_node)
workflow.add_node("professor", draft_node)
workflow.add_node("refusal", refusal_node)
workflow.add_node("critic", critique_node)

workflow.set_entry_point("researcher")

workflow.add_conditional_edges(
    "researcher",
    grade_node,
    {
        "professor": "professor",
        "refusal": "refusal"
    }
)

workflow.add_edge("professor", "critic")
workflow.add_edge("critic", END)
workflow.add_edge("refusal", END)

app = workflow.compile()

# --- RUN ENGINE ---
if __name__ == "__main__":
    print("--- J4SON.DEV Agentic Economics Engine Online ---")
    user_query = input("Ask an Economics question: ")
    inputs = {"question": user_query, "iterations": 0}
    
    for output in app.stream(inputs):
        for key, value in output.items():
            if "answer" in value:
                print("\nFINAL ANSWER:\n", value["answer"])