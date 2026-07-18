from langchain_core.tools import tool
from agent.app.core.repository.weather_repository import WeatherRepository
from typing import Optional, List

_repo = WeatherRepository()

VALID_EVENT_TYPES = {"CME", "FLR", "GST"}


@tool(response_format="content_and_artifact")
def get_space_weather_events(event_type: Optional[List[str]] = None, limit: int = 10):
    """Get recent space weather notifications from the last 30 days.

    Args:
        event_type: Optional list of types to filter by — any of 'CME' (Coronal Mass
                    Ejection), 'FLR' (Solar Flare), 'GST' (Geomagnetic Storm).
                    Omit or pass an empty list to get all types.
        limit: Max number of events to return.
    """
    if event_type:
        invalid = [e for e in event_type if e not in VALID_EVENT_TYPES]
        if invalid:
            return (
                f"Invalid event_type(s) {invalid}. Must be from: {', '.join(VALID_EVENT_TYPES)}.",
                [],
            )

    results = _repo.get_events(event_type=event_type, limit=limit)
    if not results:
        scope = f" of type {event_type}" if event_type else ""
        return f"No space weather events{scope} found in the last 30 days.", []

    lines = [f"Found {len(results)} space weather event(s):"]
    for r in results:
        lines.append(
            f"- **{r.get('message_type', 'UNKNOWN')}** at {r['event_timestamp']} — {r.get('message_url', 'no link')}"
        )
    return "\n".join(lines), results
