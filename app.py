import streamlit as st
import os
from dotenv import load_dotenv
from economics_agent import app # This imports your compiled LangGraph

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="j4son.dev Economics AI", page_icon="📈", layout="centered")

st.title("📈 j4son.dev Economics Expert")
st.markdown("---")

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input ---
if prompt := st.chat_input("Ask an Economics question..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Agent Logic with "Live Thinking"
    with st.chat_message("assistant"):
        # We use st.status to show the LangGraph steps transparently
        with st.status("🚀 Agent is thinking...", expanded=True) as status:
            inputs = {"question": prompt, "iterations": 0}
            final_answer = ""
            
            # Streaming the Graph steps to the UI
            for output in app.stream(inputs):
                for key, value in output.items():
                    node_name = key.replace("_", " ").title()
                    st.write(f"✅ **{node_name}** complete.")
                    
                    if "answer" in value:
                        final_answer = value["answer"]
            
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        # 3. Display Final Answer
        st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})