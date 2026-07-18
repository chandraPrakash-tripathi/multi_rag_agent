from langchain_core.tools import tool
from agent.app.core.repository.knowledge_repository import KnowledgeRepository

_repo = KnowledgeRepository()


@tool(response_format="content_and_artifact")
def search_scientific_knowledge(query: str, limit: int = 3):
    """Semantically search NASA scientific documentation and educational articles
    to answer conceptual questions (e.g. black holes, telescopes, mission science).

    Args:
        query: Natural language question or topic to search for.
        limit: Max number of document chunks to return.
    """
    results = _repo.search_scientific_knowledge(query, limit=limit)
    if not results:
        return f"No scientific knowledge found for: {query}", []

    lines = [f"Found {len(results)} relevant document chunk(s) for '{query}':"]
    for r in results:
        lines.append(f"- **{r['title']}** (relevance: {r['score']:.2f})\n  {r['text']}")
    return "\n".join(lines), results
