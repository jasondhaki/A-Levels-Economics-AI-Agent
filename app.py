import streamlit as st
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from economics_agent import app # Your Agentic Engine

load_dotenv()

# --- 1. SESSION INITIALIZATION (Private & Isolated) ---
# We no longer use HISTORY_FILE. Every user gets a fresh, empty dictionary.
if "history" not in st.session_state:
    st.session_state.history = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="J4SON.DEV ECONOMICS AI", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar-text { font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 14px; }
    button[kind="secondary"] { padding: 0px 5px; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: SESSION NAVIGATION ---
with st.sidebar:
    st.title("J4SON.DEV AI")
    
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
    st.subheader("🕒 SESSIONS (THIS TAB)")
    
    # Pulled purely from user's current session memory
    sessions = list(st.session_state.history.items())
    sessions.sort(key=lambda x: (not x[1].get("pinned", False), x[1].get("timestamp", "")), reverse=True)

    if not sessions:
        st.info("Sessions are private and cleared on refresh.")
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
                        st.rerun()
                    
                    st.markdown("---")
                    # PIN / UNPIN
                    is_pinned = data.get("pinned", False)
                    if st.button("📍 UNPIN" if is_pinned else "📌 PIN", key=f"pin_{chat_id}", use_container_width=True):
                        st.session_state.history[chat_id]["pinned"] = not is_pinned
                        st.rerun()
                    
                    st.markdown("---")
                    # DELETE
                    if st.button("🗑️ DELETE", key=f"del_{chat_id}", use_container_width=True, type="primary"):
                        del st.session_state.history[chat_id]
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        st.rerun()

    st.markdown("---")
    st.markdown("<p class='sidebar-text'>PRIVATE ENCRYPTED ANALYSIS</p>", unsafe_allow_html=True)

# --- 4. MAIN CHAT INTERFACE ---
st.title("📈 J4SON.DEV ECONOMICS EXPERT")
st.caption("ADVANCED ANALYSIS ENGINE FOR A-LEVEL STUDENTS")

current_id = st.session_state.current_chat_id
# Pull messages from the user's isolated history
messages = st.session_state.history.get(current_id, {}).get("messages", []) if current_id else []

# Display current session messages
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input handling
prompt = st.chat_input("Ask an Economics question...")
if "pending_input" in st.session_state:
    prompt = st.session_state.pop("pending_input")

if prompt:
    if current_id is None:
        current_id = str(uuid.uuid4())
        st.session_state.current_chat_id = current_id
        title = prompt[:25].upper() + "..." if len(prompt) > 25 else prompt.upper()
        st.session_state.history[current_id] = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "messages": [],
            "pinned": False
        }

    # Add user message to memory
    st.session_state.history[current_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)

    # Process through Agentic Engine
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
        # Store answer in memory
        st.session_state.history[current_id]["messages"].append({"role": "assistant", "content": final_answer})
        # Force rerun to update sidebar and export feature
        st.rerun()

# --- 5. EXPORT FEATURE (Privacy-Safe) ---
if current_id and current_id in st.session_state.history:
    current_messages = st.session_state.history[current_id]["messages"]
    if current_messages:
        st.markdown("---")
        st.subheader("📥 Export Knowledge")
        
        chat_text = f"J4SON.DEV ECONOMICS STUDY NOTES\n"
        chat_text += f"SESSION: {st.session_state.history[current_id]['title']}\n"
        chat_text += f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        chat_text += "="*40 + "\n\n"
        
        for msg in current_messages: 
            role = "STUDENT" if msg['role'] == "user" else "PROFESSOR"
            chat_text += f"[{role}]:\n{msg['content']}\n\n"
        
        st.download_button(
            label="📄 DOWNLOAD SESSION NOTES (.txt)", 
            data=chat_text, 
            file_name=f"Econ_Notes_{datetime.now().strftime('%m%d_%H%M')}.txt", 
            mime="text/plain",
            use_container_width=True
        )