import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from agent.app.core.graph.graph_builder import build_graph

API_KEY = os.getenv("API_KEY")

_checkpointer_cm = None
_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer_cm, _graph
    _checkpointer_cm = SqliteSaver.from_conn_string("checkpoints.db")
    checkpointer = _checkpointer_cm.__enter__()
    _graph = build_graph(checkpointer)
    yield
    _checkpointer_cm.__exit__(None, None, None)


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Space Intelligence Platform", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class QueryRequest(BaseModel):
    query: str
    thread_id: str | None = None


class QueryResponse(BaseModel):
    thread_id: str
    final_answer: str
    report: str | None = None
    errors: list[dict] = []
    completed_agents: list[str] = []
    execution_logs: list[str] = []


@app.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
def run_query(request: Request, body: QueryRequest):
    verify_api_key(request.headers.get("x-api-key"))

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    thread_id = body.thread_id or f"session_{int(time.time())}_{uuid.uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = _graph.invoke(
            {"user_query": body.query, "messages": [HumanMessage(content=body.query)]},
            config=config,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {exc}")

    return QueryResponse(
        thread_id=thread_id,
        final_answer=result.get("final_answer", ""),
        report=result.get("report"),
        errors=result.get("errors", []),
        completed_agents=result.get("completed_agents", []),
        execution_logs=result.get("execution_logs", []),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
