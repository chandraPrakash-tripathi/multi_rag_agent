# lookup.py provides knowledge retrieval tools rather than booking or update operations.
#  It initializes a VectorDB instance connected to the faq_collection in Qdrant, where company FAQs and policies are stored as embeddings.
#  The search_faq() tool performs semantic search over these embeddings to retrieve the most relevant FAQ entries based on a user's natural language query,
# returning the question, answer, category, retrieved text chunk, and similarity score.
# The lookup_policy() tool builds on this by internally calling search_faq() and formatting the retrieved answers into a readable policy response for the LLM.
# Its docstring explicitly instructs the agent to consult company policies before performing any write operations, such as updating or cancelling bookings,
# ensuring that actions comply with business rules. Unlike the other tool modules,
# lookup.py is read-only—it never modifies the SQLite database—and serves as the agent's knowledge base for answering policy-related
#  questions and validating whether requested actions are permitted before executing them.
from vectorizer.app.vectordb.vectordb import VectorDB
from agent.app.core.settings import get_settings
from langchain_core.tools import tool
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

settings = get_settings()
faq_vectordb = VectorDB(table_name="faq", collection_name="faq_collection")


@tool
def search_faq(
    query: str,
    limit: int = 2,
) -> List[Dict]:
    """Search for FAQ entries based on a natural language query."""
    search_results = faq_vectordb.search(query, limit=limit)

    faq_entries = []
    for result in search_results:
        payload = result.payload
        faq_entries.append(
            {
                "question": payload["question"],
                "answer": payload["answer"],
                "category": payload["category"],
                "chunk": payload["content"],
                "similarity": result.score,
            }
        )
    return faq_entries


@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
    Use this before making any flight changes or performing other 'write' events."""
    faq_results = search_faq(query, limit=2)
    if not faq_results:
        return "Sorry, I couldn't find any relevant policy information. Please contact support for assistance."

    policy_info = "\n\n".join(
        [f"Q: {entry['question']}\nA: {entry['answer']}" for entry in faq_results]
    )
    return f"Here's the relevant policy information:\n\n{policy_info}"
