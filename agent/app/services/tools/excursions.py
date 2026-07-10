# follows the same architecture as cars.py but is responsible for managing trip recommendations and excursions instead of car rentals.
# It initializes a VectorDB instance connected to the trip_recommendations SQLite table and the excursions_collection in Qdrant.
# The search_trip_recommendations() tool performs semantic search over the vector database, returning the most relevant excursions along with metadata such as name,
# location, keywords, details, booking status, the retrieved text chunk, and similarity score.
# The remaining tools—book_excursion(), update_excursion(), and cancel_excursion()—perform transactional
# updates directly on the SQLite database by marking an excursion as booked or cancelled, or modifying its details.
# Together, these tools enable the LLM to both retrieve the most relevant excursion recommendations
# using Qdrant and execute persistent booking-related actions through SQLite,
# following the same retrieval-plus-action pattern used throughout the project.
from vectorizer.app.vectordb.vectordb import VectorDB
from agent.app.core.settings import get_settings
from langchain_core.tools import tool
import sqlite3
from typing import Optional, List, Dict

settings = get_settings()
db = settings.SQLITE_DB_PATH
excursions_vectordb = VectorDB(
    table_name="trip_recommendations", collection_name="excursions_collection"
)


@tool
def search_trip_recommendations(
    query: str,
    limit: int = 2,
) -> List[Dict]:
    """Search for trip recommendations based on a natural language query."""
    search_results = excursions_vectordb.search(query, limit=limit)

    recommendations = []
    for result in search_results:
        payload = result.payload
        recommendations.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "location": payload["location"],
                "keywords": payload["keywords"],
                "details": payload["details"],
                "booked": payload["booked"],
                "chunk": payload["content"],
                "similarity": result.score,
            }
        )
    return recommendations


@tool
def book_excursion(recommendation_id: int) -> str:
    """Book an excursion by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET booked = 1 WHERE id = ?", (recommendation_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Excursion {recommendation_id} successfully booked."
    else:
        conn.close()
        return f"No excursion found with ID {recommendation_id}."


@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """Update an excursion's details by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET details = ? WHERE id = ?",
        (details, recommendation_id),
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Excursion {recommendation_id} successfully updated."
    else:
        conn.close()
        return f"No excursion found with ID {recommendation_id}."


@tool
def cancel_excursion(recommendation_id: int) -> str:
    """Cancel an excursion by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trip_recommendations SET booked = 0 WHERE id = ?", (recommendation_id,)
    )
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Excursion {recommendation_id} successfully cancelled."
    else:
        conn.close()
        return f"No excursion found with ID {recommendation_id}."
