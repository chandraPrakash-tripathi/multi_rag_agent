"""
FastAPI backend for the multi-agent RAG customer support system.

Wraps the compiled LangGraph `multi_agentic_graph` with a thin HTTP API so a
frontend (e.g. Streamlit) doesn't need to know anything about LangGraph,
threads, or checkpointing.

Endpoints:
    POST /chat     - send a user message, get back the assistant's reply
                      (or a "confirmation required" flag if a sensitive
                      tool, like an actual booking, is about to run)
    POST /confirm  - approve or deny a pending sensitive action
    GET  /health   - simple liveness check

Run with:
    poetry run uvicorn agent.app.api.main:app --reload --port 8000

ASSUMPTION: passenger_id defaults to "3442 587242", the standard test
passenger from the original LangGraph tutorial's travel2.sqlite sample data.
If your CLI main.py uses a different one, update DEFAULT_PASSENGER_ID below.
"""

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.app.core.graph import multi_agentic_graph
from agent.app.core.logger import logger

DEFAULT_PASSENGER_ID = "3442 587242"

app = FastAPI(title="Multi-Agent RAG Customer Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None  # if omitted, a new conversation starts
    passenger_id: str = DEFAULT_PASSENGER_ID


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    requires_confirmation: bool = False
    pending_action: Optional[str] = None


class ConfirmRequest(BaseModel):
    thread_id: str
    approve: bool
    passenger_id: str = DEFAULT_PASSENGER_ID


def _build_config(thread_id: str, passenger_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
            "passenger_id": passenger_id,
        }
    }


def _extract_last_ai_text(messages) -> str:
    """Pull the most recent AI-authored text content out of a message list."""
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or (
            msg[0] if isinstance(msg, tuple) else None
        )
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", None) or (
                msg[1] if isinstance(msg, tuple) else ""
            )
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                )
            if content:
                return content
    return ""


def _describe_pending_tool_call(state) -> Optional[str]:
    """If the graph is paused before a sensitive tool, describe what it's about to do."""
    if not state.next:
        return None
    messages = state.values.get("messages", [])
    for msg in reversed(messages):
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            call = tool_calls[0]
            return f"{call['name']}({call['args']})"
    return "a booking action"


def _reset_stuck_thread(config: dict):
    """
    Clear a thread's checkpointed state if it's left in a pending/interrupted
    state from a previous crashed request (e.g. a tool raised an exception
    mid-run), so the next /chat call doesn't get falsely blocked by a 409.
    """
    try:
        multi_agentic_graph.update_state(config, {"messages": []}, as_node="__start__")
    except Exception:
        pass  # best-effort; if this fails we still surface the original error to the client


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = _build_config(thread_id, req.passenger_id)

    current_state = multi_agentic_graph.get_state(config)
    if current_state.next:
        pending = _describe_pending_tool_call(current_state)
        raise HTTPException(
            status_code=409,
            detail=f"Thread has a pending action awaiting confirmation: {pending}. "
            f"Call /confirm before sending a new message.",
        )

    try:
        multi_agentic_graph.invoke(
            {"messages": [("user", req.message)]},
            config,
        )
    except Exception as e:
        logger.error(f"Error during graph invoke: {e}")
        raise HTTPException(
            status_code=500, detail=f"An error occurred processing your message: {e}"
        )

    new_state = multi_agentic_graph.get_state(config)
    reply = _extract_last_ai_text(new_state.values.get("messages", []))

    if new_state.next:
        pending = _describe_pending_tool_call(new_state)
        return ChatResponse(
            thread_id=thread_id,
            reply=reply or "I need your confirmation before proceeding.",
            requires_confirmation=True,
            pending_action=pending,
        )

    return ChatResponse(thread_id=thread_id, reply=reply)


@app.post("/confirm", response_model=ChatResponse)
def confirm(req: ConfirmRequest):
    config = _build_config(req.thread_id, req.passenger_id)
    current_state = multi_agentic_graph.get_state(config)

    if not current_state.next:
        raise HTTPException(
            status_code=400, detail="No pending action to confirm for this thread."
        )

    try:
        if req.approve:
            multi_agentic_graph.invoke(None, config)
        else:
            messages = current_state.values.get("messages", [])
            last_msg = messages[-1] if messages else None
            tool_call_id = None
            if last_msg is not None:
                tool_calls = getattr(last_msg, "tool_calls", None)
                if tool_calls:
                    tool_call_id = tool_calls[0]["id"]

            if tool_call_id:
                from langchain_core.messages import ToolMessage

                multi_agentic_graph.update_state(
                    config,
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call_id,
                                content="API call denied by user. Please continue assisting, "
                                "accounting for the user's input.",
                            )
                        ]
                    },
                )
            multi_agentic_graph.invoke(None, config)
    except Exception as e:
        logger.error(f"Error during graph confirm/resume: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while resolving the pending action: {e}",
        )

    new_state = multi_agentic_graph.get_state(config)
    reply = _extract_last_ai_text(new_state.values.get("messages", []))

    if new_state.next:
        pending = _describe_pending_tool_call(new_state)
        return ChatResponse(
            thread_id=req.thread_id,
            reply=reply or "I need your confirmation before proceeding.",
            requires_confirmation=True,
            pending_action=pending,
        )

    return ChatResponse(thread_id=req.thread_id, reply=reply)


@app.post("/reset/{thread_id}")
def reset_thread(thread_id: str, passenger_id: str = DEFAULT_PASSENGER_ID):
    """Utility endpoint: clear a stuck/crashed thread without restarting the server."""
    config = _build_config(thread_id, passenger_id)
    _reset_stuck_thread(config)
    return {"status": "reset", "thread_id": thread_id}
