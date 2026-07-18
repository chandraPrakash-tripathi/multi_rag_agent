from typing import Literal
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import SystemMessage, AIMessage
from agent.app.core.assistant.assistant import AssistantBase
from agent.app.core.graph.graph_state import GraphState

_SYSTEM_PROMPT = (
    "You are the final report synthesizer for a space intelligence platform. "
    "You will be given the user's original query and everything the specialist "
    "agents gathered. Write a clear, well-formatted markdown executive summary. "
    "Only include sections for data that was actually gathered — do not "
    "fabricate or reference data that isn't present. If errors occurred, "
    "mention them briefly and factually, don't hide them."
)

# Higher temperature than tool-calling agents (0.1) — this is prose synthesis,
# not structured tool selection, so some fluency/variation is appropriate.
_report_llm = AssistantBase(system_prompt=_SYSTEM_PROMPT, temperature=0.4).llm


def report_node(state: GraphState) -> Command[Literal["__end__"]]:
    context = (
        f"User query: {state.user_query}\n\n"
        f"Near-Earth Objects: {state.near_earth_objects}\n\n"
        f"Space Weather: {state.solar_events}\n\n"
        f"Earth Events: {state.natural_events}\n\n"
        f"Astronomy Picture of the Day: {state.astronomy_media}\n\n"
        f"Space News: {state.space_news}\n\n"
        f"Retrieved Knowledge: {state.retrieved_documents}\n\n"
        f"Analytics: {state.analytics}\n\n"
        f"Errors encountered: {state.errors}"
    )

    response = _report_llm.invoke(
        [SystemMessage(content=_SYSTEM_PROMPT), SystemMessage(content=context)]
    )
    final_text = response.content

    return Command(
        goto=END,
        update={
            "report": final_text,
            "final_answer": final_text,
            "messages": [AIMessage(content=final_text)],
        },
    )
