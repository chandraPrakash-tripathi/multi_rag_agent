from langchain_core.tools import tool
from agent.app.core.repository.earth_repository import EarthEventsRepository
from typing import Optional

_repo = EarthEventsRepository()


@tool(response_format="content_and_artifact")
# earth_tools.py
def get_active_earth_events(category: Optional[str] = None, limit: int = 10):
    """Get currently active (open) Earth natural events from the last 30 days,
    such as wildfires, volcanoes, or severe storms.

    Args:
        category: Filter by category, e.g. 'Wildfires', 'Volcanoes', 'Severe Storms'.
        limit: Max number of events to return.
    """
    results = _repo.get_active_events(category=category, limit=limit)
    if not results:
        scope = f" in category '{category}'" if category else ""
        return f"No active earth events{scope} found in the last 30 days.", []

    lines = [f"Found {len(results)} active earth event(s):"]
    for r in results:
        mag = (
            f", magnitude: {r['magnitude_value']} {r.get('magnitude_unit', '')}"
            if r.get("magnitude_value")
            else ""
        )
        lines.append(
            f"- **{r['title']}** ({r.get('category', 'Uncategorized')}) — since {r['event_timestamp']}{mag}"
        )
    return "\n".join(lines), results
