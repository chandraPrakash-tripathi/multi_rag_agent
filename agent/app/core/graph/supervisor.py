from typing import Literal
from langgraph.types import Command
from langchain_core.messages import SystemMessage
from agent.app.core.graph.graph_state import GraphState
from ..assistant.assistant import AssistantBase

AVAILABLE_AGENTS = {
    "neo_agent": "Near-Earth Object Agent - hazardous asteroid monitoring, closest approaches",
    "weather_agent": "Space Weather Agent - solar flares, CMEs, geomagnetic storms",
    "earth_agent": "Earth Natural Events Agent - wildfires, volcanoes, floods, storms",
    "apod_agent": "Astronomy Media Agent - explains NASA's Astronomy Picture of the Day",
    "knowledge_agent": "Space Knowledge Agent - answers scientific concept questions via RAG",
    "news_agent": "Space News Agent - latest launches, discoveries, mission updates",
    "analytics_agent": "Analytics Agent - trends/statistics on data already gathered. Only valid after at least one data-gathering agent has completed.",
}

# Lowered from 6 -> 3 for now while iterating on prompt behavior. Each cycle
# can take 60-240s on local Ollama with multiple agents, so a full 6-cycle
# run during debugging is painfully slow. Raise back to 6 once redundant
# re-selection is confirmed fixed and you're doing a real end-to-end test.
MAX_CYCLES = 3

_SYSTEM_PROMPT = (
    "You are the supervisor of a space intelligence multi-agent system.\n"
    "Given the user's query and what has been gathered so far, decide which "
    "agent(s) should run next.\n\nAvailable agents:\n"
    + "\n".join(f"- {k}: {v}" for k, v in AVAILABLE_AGENTS.items())
    + "\n\nCRITICAL RULES:\n"
    "- If an agent's status below says 'ALREADY RUN, found N item(s)' with "
    "N greater than 0, it has already succeeded — NEVER re-select it. "
    "Re-running a successful agent wastes time and produces no new "
    "information.\n"
    "- Only re-select a previously run agent if its status shows 0 items "
    "found AND you have a specific, stated reason a retry would help (e.g. "
    "a narrower or different date range). Do not retry just because you "
    "want more data — zero is a valid answer.\n"
    "- As soon as every data-gathering agent relevant to the user's query "
    "has been run at least once — regardless of whether each one found "
    "data or not — respond DONE. Finding zero results is a valid, final "
    "answer. Do not keep querying an agent hoping for a different result.\n"
    "- analytics_agent only runs after at least one data-gathering agent "
    "has already completed with results.\n"
    "- Only select agents relevant to the user's query in the first place.\n\n"
    "Respond with a comma-separated list of agent names to run next, or "
    "respond with exactly: DONE\n"
    "Nothing else — no explanation, no punctuation around the words."
)

# No tools needed for a routing decision — reuse AssistantBase purely for its
# environment-aware LLM initialization (local Ollama vs prod Groq), not its tool loop.
_supervisor_llm = AssistantBase(system_prompt=_SYSTEM_PROMPT, temperature=0.0).llm


def _agent_status_line(agent_name: str, label: str, completed: list, count: int) -> str:
    if agent_name not in completed:
        return f"- {agent_name} ({label}): not yet run"
    return f"- {agent_name} ({label}): ALREADY RUN, found {count} item(s) — do not re-run unless you have a specific reason"


def _build_context(state: GraphState) -> str:
    return (
        f"User query: {state.user_query}\n\n"
        f"Agent status:\n"
        f"{_agent_status_line('neo_agent', 'Near-Earth Objects', state.completed_agents, len(state.near_earth_objects))}\n"
        f"{_agent_status_line('weather_agent', 'Space Weather', state.completed_agents, len(state.solar_events))}\n"
        f"{_agent_status_line('earth_agent', 'Earth Events', state.completed_agents, len(state.natural_events))}\n"
        f"{_agent_status_line('apod_agent', 'Astronomy Picture', state.completed_agents, 1 if state.astronomy_media else 0)}\n"
        f"{_agent_status_line('news_agent', 'Space News', state.completed_agents, len(state.space_news))}\n"
        f"{_agent_status_line('knowledge_agent', 'Scientific Knowledge', state.completed_agents, len(state.retrieved_documents))}\n"
        f"{_agent_status_line('analytics_agent', 'Analytics', state.completed_agents, 1 if state.analytics else 0)}\n\n"
        f"Errors so far: {state.errors}"
    )


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

    context = _build_context(state)

    response = _supervisor_llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            SystemMessage(content=context),
        ]
    )
    decision = (response.content or "").strip()
    print(f"[DEBUG] Supervisor context sent:\n{context}\n")
    print(f"[DEBUG] Supervisor raw decision: {decision!r}")
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
