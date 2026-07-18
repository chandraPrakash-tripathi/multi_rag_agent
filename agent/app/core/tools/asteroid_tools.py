from langchain_core.tools import tool
from datetime import datetime
from agent.app.core.repository.asteroid_repository import AsteroidRepository

_repo = AsteroidRepository()


@tool(response_format="content_and_artifact")
def get_hazardous_asteroids(start_date: str, end_date: str):
    """Get potentially hazardous asteroids with close approaches between two dates.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
    """
    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        ed = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return (
            f"Invalid date format. Use YYYY-MM-DD. Got start_date={start_date}, end_date={end_date}.",
            [],
        )

    results = _repo.get_hazardous(sd, ed)
    if not results:
        msg = f"No hazardous asteroids found between {start_date} and {end_date}."
        return msg, []

    lines = [
        f"Found {len(results)} hazardous asteroid(s) between {start_date} and {end_date}:"
    ]
    for r in results:
        lines.append(
            f"- **{r['title']}** — miss distance: {r.get('miss_distance_km', 'N/A')} km, "
            f"velocity: {r.get('relative_velocity_kph', 'N/A')} km/h"
        )
    return (
        "\n".join(lines),
        results,
    )  # results is the raw list[dict] — this is the artifact


@tool(response_format="content_and_artifact")
def get_asteroid_closest_approaches(limit: int = 10, sort_by: str = "distance"):
    """Get the closest or fastest asteroid approaches within the last 30 days.

    Args:
        limit: Max number of asteroids to return.
        sort_by: 'distance' for closest approach, or 'speed' for fastest relative velocity.
    """
    if sort_by not in ("distance", "speed"):
        return "sort_by must be either 'distance' or 'speed'.", []

    results = _repo.get_closest_approaches(limit=limit, sort_by=sort_by)
    if not results:
        return "No asteroid data found in the last 30 days.", []

    metric = "miss_distance_km" if sort_by == "distance" else "relative_velocity_kph"
    lines = [f"Top {len(results)} asteroids by {sort_by} (last 30 days):"]
    for r in results:
        lines.append(f"- **{r['title']}** — {metric}: {r.get(metric, 'N/A')}")
    return "\n".join(lines), results
