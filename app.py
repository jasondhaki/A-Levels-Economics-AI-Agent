import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from economics_agent import app # Your Engine

load_dotenv()

# --- 1. SESSION & HISTORY UTILITIES ---
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="J4SON.DEV ECONOMICS AI", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar-text { font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 14px; }
    /* Style for the mini-menu popover */
    button[kind="secondary"] { padding: 0px 5px; border: none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: SESSION NAVIGATION ---
with st.sidebar:
    st.title("J4SON.DEV AI")
    
    if st.button("➕ NEW STUDY SESSION", use_container_width=True):
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    st.subheader("🕒 SESSIONS")
    
    # Sorting: Pinned first, then by timestamp
    sessions = list(st.session_state.history.items())
    sessions.sort(key=lambda x: (not x[1].get("pinned", False), x[1].get("timestamp", "")), reverse=True)

    if not sessions:
        st.info("No saved sessions.")
    else:
        for chat_id, data in sessions:
            # Create two columns: one for the chat link, one for the menu
            col1, col2 = st.columns([5, 1])
            
            with col1:
                pin_icon = "📌 " if data.get("pinned") else "📄 "
                if st.button(f"{pin_icon}{data['title']}", key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            
            with col2:
                # Use a popover as the "dropdown menu"
                with st.popover("⋮"):
                    # --- RENAME ---
                    new_name = st.text_input("RENAME SESSION", value=data['title'], key=f"rename_input_{chat_id}")
                    if st.button("💾 SAVE NAME", key=f"save_{chat_id}"):
                        st.session_state.history[chat_id]["title"] = new_name.upper()
                        save_history(st.session_state.history)
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # --- PIN / UNPIN ---
                    is_pinned = data.get("pinned", False)
                    pin_label = "📍 UNPIN" if is_pinned else "📌 PIN TO TOP"
                    if st.button(pin_label, key=f"pin_{chat_id}", use_container_width=True):
                        st.session_state.history[chat_id]["pinned"] = not is_pinned
                        save_history(st.session_state.history)
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # --- DELETE ---
                    if st.button("🗑️ DELETE", key=f"del_{chat_id}", use_container_width=True, type="primary"):
                        del st.session_state.history[chat_id]
                        save_history(st.session_state.history)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                        st.rerun()

    st.markdown("---")
    st.markdown("<p class='sidebar-text'>PROPRIETARY ANALYSIS ENGINE</p>", unsafe_allow_html=True)

# --- 4. MAIN CHAT INTERFACE ---
st.title("📈 J4SON.DEV ECONOMICS EXPERT")
st.caption("ADVANCED ANALYSIS ENGINE FOR A-LEVEL STUDENTS")

current_id = st.session_state.current_chat_id
messages = st.session_state.history.get(current_id, {}).get("messages", []) if current_id else []

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask an Economics question..."):
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

    st.session_state.history[current_id]["messages"].append({"role": "user", "content": prompt})
    save_history(st.session_state.history)
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🏗️ J4SON.DEV ENGINE: ANALYZING SCENARIOS...", expanded=True) as status:
            inputs = {"question": prompt, "iterations": 0}
            final_answer = ""
            for output in app.stream(inputs):
                for key, value in output.items():
                    display_names = {"researcher": "🔍 ACCESSING KNOWLEDGE...", "professor": "🧠 FORMULATING RESPONSE...", "critic": "⚖️ VERIFYING ACCURACY..."}
                    st.write(display_names.get(key, key.upper()))
                    if "answer" in value: final_answer = value["answer"]
            status.update(label="✅ ANALYSIS COMPLETE!", state="complete", expanded=False)
        st.markdown(final_answer)
        st.session_state.history[current_id]["messages"].append({"role": "assistant", "content": final_answer})
        save_history(st.session_state.history)

# --- 5. EXPORT FEATURE ---
if messages:
    st.markdown("---")
    chat_text = f"J4SON.DEV ECONOMICS STUDY NOTES\nSession: {st.session_state.history[current_id]['title']}\n" + "="*30 + "\n\n"
    for msg in messages: chat_text += f"{msg['role'].upper()}: {msg['content']}\n\n"
    st.download_button(label="📥 DOWNLOAD SESSION NOTES", data=chat_text, file_name=f"J4SON_DEV_{current_id[:8]}.txt", mime="text/plain")