import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from economics_agent import app # Your Agentic Engine

load_dotenv()

# --- 1. PRIVATE PERSISTENCE ENGINE ---
HISTORY_DIR = "user_histories"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def get_user_id():
    """Manages unique user IDs via URL query parameters."""
    # Check if a user_id already exists in the URL
    if "user_id" not in st.query_params:
        # Generate a new unique 8-character ID for a first-time visitor
        new_id = str(uuid.uuid4())[:8]
        st.query_params["user_id"] = new_id
        return new_id
    return st.query_params["user_id"]

def load_user_history(u_id):
    """Loads history from a file unique to the user ID."""
    file_path = os.path.join(HISTORY_DIR, f"history_{u_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_user_history(u_id, history):
    """Saves history to a file unique to the user ID."""
    file_path = os.path.join(HISTORY_DIR, f"history_{u_id}.json")
    with open(file_path, "w") as f:
        json.dump(history, f, indent=4)

# Initialize Session with Private ID
user_id = get_user_id()

if "history" not in st.session_state:
    st.session_state.history = load_user_history(user_id)

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="J4SON.DEV ECONOMICS AI", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar-text { font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase; }
    button[kind="secondary"] { padding: 0px 5px; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: PRIVATE NAVIGATION ---
with st.sidebar:
    st.title("J4SON.DEV AI")
    st.caption(f"🔒 Private Vault ID: {user_id}")
    
    if st.button("➕ NEW STUDY SESSION", use_container_width=True):
        st.session_state.current_chat_id = None
        if "pending_input" in st.session_state: del st.session_state.pending_input
        st.rerun()

    st.markdown("---")
    
    # --- SUGGESTED QUESTIONS ---
    st.subheader("💡 TRY ASKING")
    suggestions = [
        "Difference between movement and shift in demand?",
        "Explain how a price floor creates a surplus.",
        "Compare Market vs Planned economies."
    ]
    for sug in suggestions:
        if st.button(sug, key=f"sug_{sug}", use_container_width=True):
            st.session_state.pending_input = sug
            st.session_state.current_chat_id = None 
            st.rerun()

    st.markdown("---")
    st.subheader("🕒 YOUR HISTORY")
    
    # sessions are now pulled from the private user-specific dictionary
    sessions = list(st.session_state.history.items())
    sessions.sort(key=lambda x: (not x[1].get("pinned", False), x[1].get("timestamp", "")), reverse=True)

    if not sessions:
        st.info("No saved sessions in this vault.")
    else:
        for chat_id, data in sessions:
            col1, col2 = st.columns([5, 1])
            with col1:
                pin_icon = "📌 " if data.get("pinned") else "📄 "
                if st.button(f"{pin_icon}{data['title']}", key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                with st.popover("⋮"):
                    # RENAME
                    new_name = st.text_input("RENAME", value=data['title'], key=f"ren_{chat_id}")
                    if st.button("💾 SAVE", key=f"save_{chat_id}"):
                        st.session_state.history[chat_id]["title"] = new_name.upper()
                        save_user_history(user_id, st.session_state.history)
                        st.rerun()
                    
                    # PIN
                    is_pinned = data.get("pinned", False)
                    if st.button("📍 UNPIN" if is_pinned else "📌 PIN", key=f"pin_{chat_id}"):
                        st.session_state.history[chat_id]["pinned"] = not is_pinned
                        save_user_history(user_id, st.session_state.history)
                        st.rerun()
                    
                    # DELETE
                    if st.button("🗑️ DELETE", key=f"del_{chat_id}", type="primary"):
                        del st.session_state.history[chat_id]
                        save_user_history(user_id, st.session_state.history)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        st.rerun()

    st.markdown("---")
    st.info("💡 Tip: Bookmark your URL to access this specific history later!")

# --- 4. MAIN CHAT INTERFACE ---
st.title("📈 J4SON.DEV ECONOMICS EXPERT")
st.caption("ADVANCED ANALYSIS ENGINE FOR A-LEVEL STUDENTS")

current_id = st.session_state.current_chat_id
messages = st.session_state.history.get(current_id, {}).get("messages", []) if current_id else []

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask an Economics question...")
if "pending_input" in st.session_state:
    prompt = st.session_state.pop("pending_input")

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
    with st.chat_message("user"): 
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🏗️ J4SON.DEV ENGINE: ANALYZING...", expanded=True) as status:
            inputs = {"question": prompt, "iterations": 0}
            final_answer = ""
            for output in app.stream(inputs):
                for key, value in output.items():
                    display_names = {
                        "researcher": "🔍 ACCESSING TEXTBOOK...", 
                        "professor": "🧠 REASONING...", 
                        "critic": "⚖️ VERIFYING...",
                        "refusal": "⚠️ OUT OF SCOPE"
                    }
                    st.write(display_names.get(key, key.upper()))
                    if "answer" in value: 
                        final_answer = value["answer"]
            status.update(label="✅ ANALYSIS COMPLETE!", state="complete", expanded=False)
        
        st.markdown(final_answer)
        st.session_state.history[current_id]["messages"].append({"role": "assistant", "content": final_answer})
        save_user_history(user_id, st.session_state.history)
        st.rerun()

# --- 5. EXPORT FEATURE ---
if current_id and current_id in st.session_state.history:
    current_messages = st.session_state.history[current_id]["messages"]
    if current_messages:
        st.markdown("---")
        st.subheader("📥 Export Knowledge")
        
        chat_text = f"J4SON.DEV ECONOMICS STUDY NOTES\n"
        chat_text += f"USER VAULT: {user_id}\n"
        chat_text += f"DATE: {datetime.now().strftime('%Y-%m-%d')}\n"
        chat_text += "="*40 + "\n\n"
        
        for msg in current_messages: 
            role = "STUDENT" if msg['role'] == "user" else "PROFESSOR"
            chat_text += f"[{role}]:\n{msg['content']}\n\n"
        
        st.download_button(
            label="📄 DOWNLOAD SESSION NOTES (.txt)", 
            data=chat_text, 
            file_name=f"Econ_Notes_{user_id}_{datetime.now().strftime('%m%d')}.txt", 
            mime="text/plain",
            use_container_width=True
        )