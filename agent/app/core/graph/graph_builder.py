from langgraph.graph import StateGraph, START
from langgraph.checkpoint.sqlite import SqliteSaver
from graph.graph_state import GraphState
from graph.supervisor import supervisor_node
from agents.agent_node_factory import make_agent_node
from assistant.assistant import AssistantBase
from tools.asteroid_tools import (
    get_hazardous_asteroids,
    get_asteroid_closest_approaches,
)

# ... same import pattern for weather_tools, earth_tools, apod_tools, knowledge_tools, news_tools

# --- NEO Agent ---
neo_tools = [get_hazardous_asteroids, get_asteroid_closest_approaches]
neo_assistant = AssistantBase(
    system_prompt="You monitor near-Earth objects. Use your tools to answer questions about hazardous asteroids and close approaches.",
    tools=neo_tools,
)
neo_node = make_agent_node(
    name="neo_agent",
    assistant=neo_assistant,
    tool_map={t.name: t for t in neo_tools},
    state_key="near_earth_objects",
)

# ... repeat for weather_agent, earth_agent, apod_agent, news_agent using their
#     respective tool modules and state_key ("solar_events", "natural_events",
#     "astronomy_media", "space_news")

builder = StateGraph(GraphState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("neo_agent", neo_node)
# builder.add_node("weather_agent", weather_node)
# builder.add_node("earth_agent", earth_node)
# builder.add_node("apod_agent", apod_node)
# builder.add_node("news_agent", news_node)
# builder.add_node("knowledge_agent", knowledge_node)
# builder.add_node("analytics_agent", analytics_node)
# builder.add_node("report_agent", report_node)

builder.add_edge(START, "supervisor")
# No other add_edge calls needed — every specialist node returns
# Command(goto="supervisor", ...) itself, and the supervisor's Command
# decides the next hop each cycle. This is the "edgeless" pattern current
# LangGraph favors for supervisor topologies — routing lives in the nodes,
# not in a separate edge-definition step.

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
