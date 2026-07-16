from langchain_core.tools import tool
from agent.app.core.repository.news_repository import NewsRepository
from agent.app.core.repository.knowledge_repository import KnowledgeRepository

_news_repo = NewsRepository()
_knowledge_repo = KnowledgeRepository()


@tool
def get_latest_space_news(limit: int = 10) -> str:
    """Get the most recently published spaceflight news articles.

    Args:
        limit: Max number of articles to return.
    """
    results = _news_repo.get_latest(limit=limit)
    if not results:
        return "No spaceflight news articles found."

    lines = [f"Latest {len(results)} spaceflight news article(s):"]
    for r in results:
        lines.append(
            f"- **{r['title']}** ({r.get('published_at', 'date unknown')}) — {r.get('source_url', '')}"
        )
    return "\n".join(lines)


@tool
def search_news_archives(query: str, limit: int = 5) -> str:
    """Semantically search historical spaceflight news articles for a topic or mission.

    Args:
        query: Natural language search query, e.g. 'SpaceX Starship test flights'.
        limit: Max number of articles to return.
    """
    results = _knowledge_repo.search_news_archives(query, limit=limit)
    if not results:
        return f"No news archive results found for: {query}"

    lines = [f"Found {len(results)} relevant article(s) for '{query}':"]
    for r in results:
        lines.append(
            f"- **{r['title']}** (relevance: {r['score']:.2f})\n  {r['text'][:300]}..."
        )
    return "\n".join(lines)
