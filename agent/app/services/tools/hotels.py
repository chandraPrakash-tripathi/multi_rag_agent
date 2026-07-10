# implements all the LLM-accessible tools for hotel-related operations by combining semantic retrieval with transactional database updates.
#  It initializes a VectorDB instance connected to the hotels_collection in Qdrant and the hotels table in SQLite.
# The search_hotels() tool performs semantic search over hotel embeddings to retrieve the most relevant hotels based on a natural language query,
# returning metadata such as hotel name, location, price tier, check-in/check-out dates, booking status,
# the retrieved text chunk, and similarity score.
# The remaining tools—book_hotel(), update_hotel(), and cancel_hotel()—perform persistent updates on the SQLite database by booking a hotel,
# modifying its check-in/check-out dates, or cancelling the booking through SQL UPDATE statements.
# Like the other domain-specific tool modules, this file follows the retrieval-plus-action pattern,
# where Qdrant is responsible for semantic search and SQLite serves as the source of truth for booking operations,
#  enabling the agent to both recommend suitable hotels and execute booking-related actions.
from vectorizer.app.vectordb.vectordb import VectorDB
from agent.app.core.settings import get_settings
from langchain_core.tools import tool
import sqlite3
from typing import Optional, Union, List, Dict
from datetime import datetime, date

settings = get_settings()
db = settings.SQLITE_DB_PATH
hotels_vectordb = VectorDB(table_name="hotels", collection_name="hotels_collection")


@tool
def search_hotels(
    query: str,
    limit: int = 2,
) -> List[Dict]:
    """Search for hotels based on a natural language query."""
    search_results = hotels_vectordb.search(query, limit=limit)

    hotels = []
    for result in search_results:
        payload = result.payload
        hotels.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "location": payload["location"],
                "price_tier": payload["price_tier"],
                "checkin_date": payload["checkin_date"],
                "checkout_date": payload["checkout_date"],
                "booked": payload["booked"],
                "chunk": payload["content"],
                "similarity": result.score,
            }
        )
    return hotels


@tool
def book_hotel(hotel_id: int) -> str:
    """Book a hotel by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully booked."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."


@tool
def update_hotel(
    hotel_id: int,
    checkin_date: Optional[Union[datetime, date]] = None,
    checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """Update a hotel's check-in and check-out dates by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    if checkin_date:
        cursor.execute(
            "UPDATE hotels SET checkin_date = ? WHERE id = ?",
            (checkin_date.strftime("%Y-%m-%d"), hotel_id),
        )
    if checkout_date:
        cursor.execute(
            "UPDATE hotels SET checkout_date = ? WHERE id = ?",
            (checkout_date.strftime("%Y-%m-%d"), hotel_id),
        )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully updated."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."


@tool
def cancel_hotel(hotel_id: int) -> str:
    """Cancel a hotel by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully cancelled."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."
