from typing import Literal
from langgraph.types import Command
from langchain_core.messages import SystemMessage
from agent.app.core.graph.graph_state import GraphState
from assistant.assistant import AssistantBase

AVAILABLE_AGENTS = {
    "neo_agent": "Near-Earth Object Agent - hazardous asteroid monitoring, closest approaches",
    "weather_agent": "Space Weather Agent - solar flares, CMEs, geomagnetic storms",
    "earth_agent": "Earth Natural Events Agent - wildfires, volcanoes, floods, storms",
    "apod_agent": "Astronomy Media Agent - explains NASA's Astronomy Picture of the Day",
    "knowledge_agent": "Space Knowledge Agent - answers scientific concept questions via RAG",
    "news_agent": "Space News Agent - latest launches, discoveries, mission updates",
    "analytics_agent": "Analytics Agent - trends/statistics on data already gathered. Only valid after at least one data-gathering agent has completed.",
}

MAX_CYCLES = 6  # hard ceiling, independent of what the LLM decides

_SYSTEM_PROMPT = (
    "You are the supervisor of a space intelligence multi-agent system.\n"
    "Given the user's query and what has been gathered so far, decide which "
    "agent(s) should run next.\n\nAvailable agents:\n"
    + "\n".join(f"- {k}: {v}" for k, v in AVAILABLE_AGENTS.items())
    + "\n\nRules:\n"
    "- Only select agents relevant to the user's query.\n"
    "- Do not re-select an agent already in completed_agents unless new "
    "information genuinely requires it.\n"
    "- analytics_agent only runs after at least one data-gathering agent has "
    "already completed.\n"
    "- Once enough information has been gathered to answer the query, "
    "respond with exactly: DONE\n\n"
    "Respond with a comma-separated list of agent names to run next, or DONE. "
    "Nothing else."
)

# No tools needed for a routing decision — reuse AssistantBase purely for its
# environment-aware LLM initialization (local Ollama vs prod Groq), not its tool loop.
_supervisor_llm = AssistantBase(system_prompt=_SYSTEM_PROMPT, temperature=0.0).llm


def supervisor_node(state: GraphState) -> Command[
    Literal[
        "neo_agent",
        "weather_agent",
        "earth_agent",
        "apod_agent",
        "knowledge_agent",
        "news_agent",
        "analytics_agent",
        "report_agent",
    ]
]:
    if state.cycle_count >= MAX_CYCLES:
        return Command(
            goto="report_agent",
            update={
                "execution_logs": [
                    f"Max cycles ({MAX_CYCLES}) reached — forcing synthesis."
                ]
            },
        )

    context = (
        f"User query: {state.user_query}\n"
        f"Completed agents: {state.completed_agents}\n"
        f"Errors so far: {state.errors}\n"
        f"Data collected — NEO: {len(state.near_earth_objects)}, "
        f"Weather: {len(state.solar_events)}, Earth: {len(state.natural_events)}, "
        f"APOD: {'yes' if state.astronomy_media else 'no'}, "
        f"News: {len(state.space_news)}, Knowledge docs: {len(state.retrieved_documents)}"
    )

    response = _supervisor_llm.invoke([SystemMessage(content=context)])
    decision = (response.content or "").strip()
    log_entry = f"Supervisor cycle {state.cycle_count}: '{decision}'"

    if decision.upper() == "DONE":
        return Command(goto="report_agent", update={"execution_logs": [log_entry]})

    next_agents = [
        a.strip() for a in decision.split(",") if a.strip() in AVAILABLE_AGENTS
    ]

    if not next_agents:
        # Unparseable response — fail safe to synthesis rather than loop on garbage output.
        return Command(
            goto="report_agent",
            update={
                "execution_logs": [log_entry + " (unparseable — routing to report)"]
            },
        )

    return Command(
        goto=next_agents,  # multiple node names -> LangGraph schedules them in the same superstep (parallel)
        update={
            "required_agents": next_agents,
            "execution_logs": [log_entry],
            "cycle_count": state.cycle_count + 1,
        },
    )
