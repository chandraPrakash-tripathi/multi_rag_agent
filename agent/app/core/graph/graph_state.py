from typing import Annotated, Optional, Sequence
from operator import add
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(BaseModel):
    """
    Working memory for a single request. Destroyed after the request finishes —
    never a persistence layer. Structured/unstructured data lives in
    unified_layer.db and Qdrant; this only holds what the current graph run
    is actively reasoning over.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ---- Layer 1: Conversation ----
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list
    )
    user_query: str = ""
    conversation_id: str = ""

    # ---- Layer 2: Routing (decided dynamically, not pre-set) ----
    intent: Optional[str] = None
    required_agents: list[str] = Field(default_factory=list)
    execution_plan: Optional[str] = None

    # ---- Layer 3: Domain Data ----
    # Each written by exactly one dedicated agent, even under parallel fan-out —
    # no reducer needed since there's no concurrent-write collision on these keys.
    near_earth_objects: list[dict] = Field(default_factory=list)
    solar_events: list[dict] = Field(default_factory=list)
    natural_events: list[dict] = Field(default_factory=list)
    astronomy_media: Optional[dict] = None
    space_news: list[dict] = Field(default_factory=list)

    # ---- Layer 4: Knowledge ----
    retrieved_documents: list[dict] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)

    # ---- Layer 5: Intelligence ----
    analytics: Optional[dict] = None
    summaries: Optional[str] = None
    risk_scores: Optional[dict] = None
    comparisons: Optional[dict] = None
    confidence: Optional[float] = None

    # ---- Layer 6: Output ----
    final_answer: Optional[str] = None
    report: Optional[str] = None
    charts: list[dict] = Field(default_factory=list)

    # ---- Layer 7: System ----
    # Multiple agents can append to these independently, including in the same
    # parallel super-step — operator.add merges rather than overwrites.
    cycle_count: int = 0
    errors: Annotated[list[dict], add] = Field(default_factory=list)
    execution_logs: Annotated[list[str], add] = Field(default_factory=list)
    completed_agents: Annotated[list[str], add] = Field(default_factory=list)
    execution_time: Optional[float] = None
    # graph_state.py — add near cycle_count in Layer 7
    audit_cycle_count: int = 0
