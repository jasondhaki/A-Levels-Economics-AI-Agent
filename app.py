import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from economics_agent import app # Your Agentic Engine

load_dotenv()

# --- 1. PRIVATE PERSISTENCE ENGINE ---
# Create a dedicated folder on the server to store private JSON vaults
HISTORY_DIR = "user_histories"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def load_user_history(u_id):
    """Loads a specific vault file based on the ID."""
    file_path = os.path.join(HISTORY_DIR, f"history_{u_id.upper()}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_user_history(u_id, history):
    """Saves the current session data into the user's private vault."""
    file_path = os.path.join(HISTORY_DIR, f"history_{u_id.upper()}.json")
    with open(file_path, "w") as f:
        json.dump(history, f, indent=4)

# --- 2. USER ID & VAULT INITIALIZATION ---
# Priority: 1. URL Parameter -> 2. Session Memory -> 3. New Random Key
if "user_id" not in st.session_state:
    query_id = st.query_params.get("user_id")
    if query_id:
        st.session_state.user_id = query_id.upper()
    else:
        # Generate a short 4-digit unique recovery key
        st.session_state.user_id = str(uuid.uuid4()).split('-')[0][:4].upper()

user_id = st.session_state.user_id
st.query_params["user_id"] = user_id # Keep the URL updated

# Load the history belonging to this specific key
if "history" not in st.session_state or st.session_state.get("last_loaded_id") != user_id:
    st.session_state.history = load_user_history(user_id)
    st.session_state.last_loaded_id = user_id

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- 3. PAGE CONFIG ---
st.set_page_config(page_title="J4SON.DEV ECONOMICS AI", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar-header { font-size: 14px; font-weight: bold; color: #1E88E5; margin-top: 15px; text-transform: uppercase; }
    .vault-key { background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-family: monospace; font-weight: bold; font-size: 18px; text-align: center; border: 1px solid #d1d4d9; }
    button[kind="secondary"] { padding: 0px 5px; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR: VAULT & NAVIGATION ---
with st.sidebar:
    st.title("J4SON.DEV AI")
    
    # --- VAULT KEY & RECOVERY ---
    st.markdown("<p class='sidebar-header'>🔐 YOUR PRIVATE VAULT KEY</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='vault-key'>{user_id}</div>", unsafe_allow_html=True)
    st.caption("Write this down or bookmark the URL to resume your history later.")
    
    with st.expander("🔄 RESTORE OLD SESSION"):
        restore_key = st.text_input("ENTER KEY", placeholder="e.g. A1B2").upper()
        if st.button("UNLOCK VAULT", use_container_width=True):
            st.session_state.user_id = restore_key
            st.query_params["user_id"] = restore_key
            st.rerun()

    st.markdown("---")
    
    if st.button("➕ NEW STUDY SESSION", use_container_width=True):
        st.session_state.current_chat_id = None
        st.rerun()

    # --- HISTORY LIST ---
    st.markdown("<p class='sidebar-header'>🕒 VAULT HISTORY</p>", unsafe_allow_html=True)
    sessions = list(st.session_state.history.items())
    sessions.sort(key=lambda x: (not x[1].get("pinned", False), x[1].get("timestamp", "")), reverse=True)

    if not sessions:
        st.info("This vault is currently empty.")
    else:
        for chat_id, data in sessions:
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(f"📄 {data['title']}", key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    del st.session_state.history[chat_id]
                    save_user_history(user_id, st.session_state.history)
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = None
                    st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
st.title("📈 J4SON.DEV ECONOMICS EXPERT")
current_id = st.session_state.current_chat_id
messages = st.session_state.history.get(current_id, {}).get("messages", []) if current_id else []

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask an Economics question...")

if prompt:
    if current_id is None:
        current_id = str(uuid.uuid4())
        st.session_state.current_chat_id = current_id
        st.session_state.history[current_id] = {
            "title": prompt[:25].upper() + "...",
            "timestamp": datetime.now().isoformat(),
            "messages": [],
            "pinned": False
        }

    st.session_state.history[current_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🏗️ ANALYZING SCENARIO...", expanded=True) as status:
            inputs = {"question": prompt, "iterations": 0}
            final_answer = ""
            for output in app.stream(inputs):
                for key, value in output.items():
                    if "answer" in value: final_answer = value["answer"]
            status.update(label="✅ COMPLETE!", state="complete", expanded=False)
        
        st.markdown(final_answer)
        st.session_state.history[current_id]["messages"].append({"role": "assistant", "content": final_answer})
        save_user_history(user_id, st.session_state.history)
        st.rerun()

# --- 6. EXPORT ---
if current_id and current_id in st.session_state.history:
    curr_messages = st.session_state.history[current_id]["messages"]
    if curr_messages:
        st.markdown("---")
        st.subheader("📥 Export Knowledge")
        chat_text = f"J4SON.DEV ECONOMICS NOTES | VAULT: {user_id}\n" + "="*40 + "\n\n"
        for m in curr_messages:
            role = "STUDENT" if m['role'] == 'user' else "PROFESSOR"
            chat_text += f"[{role}]:\n{m['content']}\n\n"
        
        st.download_button(label="📄 DOWNLOAD NOTES", data=chat_text, 
                           file_name=f"Econ_Notes_{user_id}.txt", use_container_width=True)