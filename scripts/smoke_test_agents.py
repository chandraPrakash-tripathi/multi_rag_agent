from agent.app.core.graph.graph_state import GraphState
from agent.app.core.graph.graph_builder import (
    build_neo_node,
    build_weather_node,
    build_earth_node,
    build_apod_node,
    build_news_node,
    build_knowledge_node,
)
from agent.app.core.agents.analytics_agent import analytics_node
from agent.app.core.agents.report_agent import report_node

TESTS = [
    (
        "weather_agent",
        build_weather_node(),
        "Are there any solar flares or CMEs recently?",
        "solar_events",
    ),
    (
        "earth_agent",
        build_earth_node(),
        "Show me active wildfires right now.",
        "natural_events",
    ),
    (
        "apod_agent",
        build_apod_node(),
        "Explain today's astronomy picture of the day.",
        "astronomy_media",
    ),
    ("news_agent", build_news_node(), "What's the latest space news?", "space_news"),
    (
        "knowledge_agent",
        build_knowledge_node(),
        "Explain how black holes form.",
        "retrieved_documents",
    ),
]

for name, node_fn, query, state_key in TESTS:
    print(f"\n{'='*50}\nTesting: {name}\n{'='*50}")
    state = GraphState(user_query=query)
    try:
        command = node_fn(state)
        result_value = command.update.get(state_key)
        print(f"[{name}] state_key '{state_key}' result: {result_value}")
        print(f"[{name}] completed_agents: {command.update.get('completed_agents')}")
    except Exception as exc:
        print(f"[{name}] CRASHED: {exc}")

# Analytics needs pre-populated state to have anything to compute on
print(f"\n{'='*50}\nTesting: analytics_agent\n{'='*50}")
fake_state = GraphState(
    user_query="test",
    near_earth_objects=[
        {
            "title": "Test Asteroid A",
            "relative_velocity_kph": 50000,
            "miss_distance_km": 100000,
        },
        {
            "title": "Test Asteroid B",
            "relative_velocity_kph": 70000,
            "miss_distance_km": 200000,
        },
    ],
)
command = analytics_node(fake_state)
print(f"[analytics_agent] analytics: {command.update.get('analytics')}")
print(f"[analytics_agent] charts: {command.update.get('charts')}")

# Report needs some populated state to synthesize from
print(f"\n{'='*50}\nTesting: report_agent\n{'='*50}")
command = report_node(fake_state)
print(f"[report_agent] final_answer:\n{command.update.get('final_answer')}")
