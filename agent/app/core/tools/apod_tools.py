from langchain_core.tools import tool
from datetime import datetime
from agent.app.core.repository.apod_repository import ApodRepository

_repo = ApodRepository()


@tool(response_format="content_and_artifact")
def get_apod_by_date(date: str):
    """Get NASA's Astronomy Picture of the Day for a specific date.

    Args:
        date: Date in YYYY-MM-DD format.
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"Invalid date format. Use YYYY-MM-DD. Got: {date}.", {}

    result = _repo.get_by_date(date)
    if not result:
        return f"No APOD entry found for {date}.", {}

    content = f"**{result['title']}** ({date})\n\n{result['content']}\n\nImage: {result.get('source_url', 'N/A')}"
    return (
        content,
        result,
    )  # single dict artifact, not a list — matches astronomy_media's Optional[dict] shape
