from langgraph.graph import StateGraph, START
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid
from agent.app.core.agents.auditor_agent import auditor_node
from agent.app.core.graph.graph_state import GraphState
from agent.app.core.graph.supervisor import supervisor_node
from agent.app.core.agents.agent_node_factory import make_agent_node
from agent.app.core.agents.analytics_agent import analytics_node
from agent.app.core.agents.report_agent import report_node
from agent.app.core.assistant.assistant import AssistantBase

from agent.app.core.tools.asteroid_tools import (
    get_hazardous_asteroids,
    get_asteroid_closest_approaches,
)
from agent.app.core.tools.weather_tools import get_space_weather_events
from agent.app.core.tools.earth_tools import get_active_earth_events
from agent.app.core.tools.apod_tools import get_apod_by_date
from agent.app.core.tools.news_tools import get_latest_space_news, search_news_archives
from agent.app.core.tools.knowledge_tools import search_scientific_knowledge


def build_neo_node():
    tools = [get_hazardous_asteroids, get_asteroid_closest_approaches]
    assistant = AssistantBase(
        system_prompt="You monitor near-Earth objects. Use your tools to answer questions about hazardous asteroids and close approaches.",
        tools=tools,
    )
    return make_agent_node(
        "neo_agent",
        assistant,
        {t.name: t for t in tools},
        state_key="near_earth_objects",
    )


def build_weather_node():
    tools = [get_space_weather_events]
    assistant = AssistantBase(
        system_prompt="You monitor space weather. Use your tools to answer questions about solar flares, CMEs, and geomagnetic storms.",
        tools=tools,
    )
    return make_agent_node(
        "weather_agent", assistant, {t.name: t for t in tools}, state_key="solar_events"
    )


def build_earth_node():
    tools = [get_active_earth_events]
    assistant = AssistantBase(
        system_prompt="You monitor Earth natural events. Use your tools to answer questions about wildfires, volcanoes, floods, and storms.",
        tools=tools,
    )
    return make_agent_node(
        "earth_agent", assistant, {t.name: t for t in tools}, state_key="natural_events"
    )


def build_apod_node():
    tools = [get_apod_by_date]
    assistant = AssistantBase(
        system_prompt="You explain NASA's Astronomy Picture of the Day. Use your tool to fetch and explain the APOD for a given date.",
        tools=tools,
    )
    return make_agent_node(
        "apod_agent",
        assistant,
        {t.name: t for t in tools},
        state_key="astronomy_media",
        merge=lambda artifacts: (artifacts[-1] if artifacts else None),
    )


def build_news_node():
    tools = [get_latest_space_news, search_news_archives]
    assistant = AssistantBase(
        system_prompt="You cover space news. Use get_latest_space_news for recent headlines and search_news_archives for historical/topic-specific queries.",
        tools=tools,
    )
    return make_agent_node(
        "news_agent", assistant, {t.name: t for t in tools}, state_key="space_news"
    )


def build_knowledge_node():
    tools = [search_scientific_knowledge]
    assistant = AssistantBase(
        system_prompt="You answer scientific questions about space topics using semantic search over NASA documentation.",
        tools=tools,
    )
    return make_agent_node(
        "knowledge_agent",
        assistant,
        {t.name: t for t in tools},
        state_key="retrieved_documents",
    )


def build_graph(checkpointer):
    builder = StateGraph(GraphState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("neo_agent", build_neo_node())
    builder.add_node("weather_agent", build_weather_node())
    builder.add_node("earth_agent", build_earth_node())
    builder.add_node("apod_agent", build_apod_node())
    builder.add_node("news_agent", build_news_node())
    builder.add_node("knowledge_agent", build_knowledge_node())
    builder.add_node("analytics_agent", analytics_node)
    builder.add_node(
        "auditor_agent", auditor_node
    )  # <-- add here, alongside the others
    builder.add_node("report_agent", report_node)

    builder.add_edge(START, "supervisor")
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        graph = build_graph(checkpointer)

        config = {"configurable": {"thread_id": f"test_{uuid.uuid4().hex[:8]}"}}
        result = graph.invoke(
            {
                "user_query": "Are there any active wildfires or solar storms right now?",
                "messages": [
                    HumanMessage(
                        content="Are there any active wildfires or solar storms right now?"
                    )
                ],
            },
            config={"configurable": {"thread_id": f"test_{uuid.uuid4().hex[:8]}"}},
        )
        print(result["final_answer"])
