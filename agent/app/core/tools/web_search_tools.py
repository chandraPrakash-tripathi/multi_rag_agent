import os
import logging

from langchain_core.tools import tool
import serpapi

logger = logging.getLogger(__name__)
from dotenv import load_dotenv

# This finds your .env file and loads its variables into Python's os environment
load_dotenv()
_SERPAPI_KEY = os.getenv("SERPAPI_KEY")
# Built once at import time (mirrors the _news_repo/_knowledge_repo singleton
# pattern in news_tools.py). None if unset — the tool degrades to a clear
# error message instead of crashing the agent node.
_client = serpapi.Client(api_key=_SERPAPI_KEY) if _SERPAPI_KEY else None


@tool(response_format="content_and_artifact")
def web_search_fallback(query: str, num_results: int = 5):
    """LAST RESORT general web search (Google, via SerpAPI). Costs a paid API
    call, so only use this after get_latest_space_news and/or
    search_news_archives have already been tried for this query in this
    same conversation and returned no relevant results.

    Use this only for queries outside NASA/spaceflight-news coverage —
    e.g. a specific company's stock move, a general how-to question, or
    a topic unrelated to space. Do not use this as your first tool call.

    Args:
        query: The search query.
        num_results: Max number of results to return (default 5).
    """
    if _client is None:
        return "Web search is not configured (SERPAPI_KEY missing).", []

    try:
        results = _client.search({"engine": "google", "q": query, "num": num_results})
    except Exception as exc:
        logger.warning("SerpAPI search failed for %r: %s", query, exc)
        return f"Web search failed: {exc}", []

    organic = results.get("organic_results", [])
    if not organic:
        return f"No web results found for: {query}", []

    items = [
        {
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet"),
        }
        for r in organic[:num_results]
    ]

    lines = [f"Found {len(items)} web result(s) for '{query}' (general web fallback):"]
    for item in items:
        lines.append(
            f"- **{item['title']}** — {item['link']}\n  {item.get('snippet', '')}"
        )

    return "\n".join(lines), items
