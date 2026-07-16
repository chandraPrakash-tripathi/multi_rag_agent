from langchain_core.tools import tool
from agent.app.core.repository.weather_repository import WeatherRepository

_repo = WeatherRepository()

VALID_EVENT_TYPES = {"CME", "FLR", "GST"}


@tool
def get_space_weather_events(event_type: str = None, limit: int = 10) -> str:
    """Get recent space weather notifications from the last 30 days.

    Args:
        event_type: Filter by type — 'CME' (Coronal Mass Ejection), 'FLR' (Solar Flare),
                    'GST' (Geomagnetic Storm). Omit to get all types.
        limit: Max number of events to return.
    """
    if event_type and event_type not in VALID_EVENT_TYPES:
        return f"Invalid event_type '{event_type}'. Must be one of: {', '.join(VALID_EVENT_TYPES)}."

    results = _repo.get_events(event_type=event_type, limit=limit)
    if not results:
        scope = f" of type {event_type}" if event_type else ""
        return f"No space weather events{scope} found in the last 30 days."

    lines = [f"Found {len(results)} space weather event(s):"]
    for r in results:
        lines.append(
            f"- **{r.get('message_type', 'UNKNOWN')}** at {r['event_timestamp']} — {r.get('message_url', 'no link')}"
        )
    return "\n".join(lines)
