"""
Streamlit chat frontend for the multi-agent RAG customer support system.

Talks to the FastAPI backend (agent/app/api/main.py) over HTTP - no LangGraph
imports here, this file only knows about /chat and /confirm.

Run with:
    poetry run streamlit run streamlit_app.py

Make sure the FastAPI backend is already running on http://localhost:8000
(poetry run uvicorn agent.app.api.main:app --port 8000) before starting this.
"""

import uuid

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Travel Assistant", page_icon="✈️", layout="centered")
st.title("✈️ Multi-Agent Travel Support")

# --- Session state setup ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = (
        []
    )  # list of {"role": "user"/"assistant", "content": str}
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None  # description string, or None

with st.sidebar:
    st.caption(f"Thread ID: `{st.session_state.thread_id}`")
    if st.button("Start new conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_action = None
        st.rerun()

# --- Render chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Pending confirmation UI (blocks new input until resolved) ---
if st.session_state.pending_action:
    st.warning(f"⚠️ Confirmation needed: **{st.session_state.pending_action}**")
    col1, col2 = st.columns(2)

    def _resolve(approve: bool):
        try:
            resp = requests.post(
                f"{API_BASE_URL}/confirm",
                json={"thread_id": st.session_state.thread_id, "approve": approve},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Error: {e}"}
            )
            st.session_state.pending_action = None
            st.rerun()
            return

        st.session_state.messages.append(
            {"role": "assistant", "content": data["reply"]}
        )
        st.session_state.pending_action = (
            data["pending_action"] if data["requires_confirmation"] else None
        )
        st.rerun()

    with col1:
        if st.button("✅ Approve", use_container_width=True):
            _resolve(True)
    with col2:
        if st.button("❌ Deny", use_container_width=True):
            _resolve(False)

# --- Chat input (disabled while a confirmation is pending) ---
user_input = st.chat_input(
    "Ask about flights, hotels, car rentals, or excursions...",
    disabled=bool(st.session_state.pending_action),
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "message": user_input,
                        "thread_id": st.session_state.thread_id,
                    },
                    timeout=120,  # local CPU inference can be slow - give it room
                )
                resp.raise_for_status()
                data = resp.json()
                st.markdown(data["reply"])
            except requests.RequestException as e:
                st.error(f"Error contacting backend: {e}")
                data = None

    if data:
        st.session_state.messages.append(
            {"role": "assistant", "content": data["reply"]}
        )
        if data["requires_confirmation"]:
            st.session_state.pending_action = data["pending_action"]
            st.rerun()
