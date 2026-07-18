from typing import Literal
from langgraph.types import Command
from agent.app.core.graph.graph_state import GraphState


def _calculate_trend_statistics(data: list[dict], field: str) -> dict:
    values = [d.get(field) for d in data if isinstance(d.get(field), (int, float))]
    if not values:
        return {"field": field, "count": 0}
    return {
        "field": field,
        "count": len(values),
        "average": sum(values) / len(values),
        "max": max(values),
        "min": min(values),
    }


def _generate_chart_config(data: list[dict], x_field: str, y_field: str) -> dict:
    return {
        "type": "bar",
        "x": [d.get(x_field) for d in data],
        "y": [d.get(y_field) for d in data],
    }


def analytics_node(state: GraphState) -> Command[Literal["supervisor"]]:
    analytics = {}
    charts = []

    if state.near_earth_objects:
        analytics["asteroid_velocity"] = _calculate_trend_statistics(
            state.near_earth_objects, "relative_velocity_kph"
        )
        analytics["asteroid_distance"] = _calculate_trend_statistics(
            state.near_earth_objects, "miss_distance_km"
        )
        charts.append(
            _generate_chart_config(
                state.near_earth_objects, "title", "miss_distance_km"
            )
        )

    if state.natural_events:
        analytics["earth_event_magnitude"] = _calculate_trend_statistics(
            state.natural_events, "magnitude_value"
        )

    return Command(
        goto="supervisor",
        update={
            "analytics": analytics,
            "charts": charts,
            "completed_agents": ["analytics_agent"],
        },
    )
