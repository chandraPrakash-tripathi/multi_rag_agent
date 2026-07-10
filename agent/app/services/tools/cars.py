# defines all the LLM-accessible tools related to car rentals.
# Using the @tool decorator, each function becomes callable by the LangChain/LangGraph agent whenever it decides an external action is needed.
# The search_car_rentals() tool performs semantic retrieval by querying the car_rentals_collection in Qdrant through the VectorDB wrapper,
# returning the most relevant rental options along with their metadata and similarity scores.
# The remaining tools—book_car_rental(), update_car_rental(), and cancel_car_rental()—perform transactional operations directly on the SQLite database,
# updating booking status or rental dates using SQL UPDATE statements.
# This separation of responsibilities follows a common RAG architecture where Qdrant is used for intelligent retrieval of relevant information,
# while SQLite serves as the source of truth for persistent booking data,
# allowing the agent to both search for rentals and execute real-world actions on them.
# Example:
# Qdrant answers: "Which rentals are most relevant to the user's query?"
# SQLite records: "This rental is now booked."
# In a production system
# In a real travel company, these SQLite updates would typically be replaced by API calls to the company's booking system or another transactional database
from vectorizer.app.vectordb.vectordb import VectorDB
from agent.app.core.settings import get_settings
from langchain_core.tools import tool
import sqlite3
from typing import List, Dict, Optional, Union
from datetime import datetime, date

settings = get_settings()
db = settings.SQLITE_DB_PATH


cars_vectordb = VectorDB(
    table_name="car_rentals", collection_name="car_rentals_collection"
)


@tool
def search_car_rentals(
    query: str,
    limit: int = 2,
) -> List[Dict]:
    """Search for car rentals based on a natural language query."""
    search_results = cars_vectordb.search(query, limit=limit)

    rentals = []
    for result in search_results:
        payload = result.payload
        rentals.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "location": payload["location"],
                "price_tier": payload["price_tier"],
                "start_date": payload["start_date"],
                "end_date": payload["end_date"],
                "booked": payload["booked"],
                "chunk": payload["content"],
                "similarity": result.score,
            }
        )
    return rentals


@tool
def book_car_rental(rental_id: int) -> str:
    """Book a car rental by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully booked."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."


@tool
def update_car_rental(
    rental_id: int,
    start_date: Optional[Union[datetime, date]] = None,
    end_date: Optional[Union[datetime, date]] = None,
) -> str:
    """Update a car rental's start and end dates by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    if start_date:
        cursor.execute(
            "UPDATE car_rentals SET start_date = ? WHERE id = ?",
            (start_date.strftime("%Y-%m-%d"), rental_id),
        )
    if end_date:
        cursor.execute(
            "UPDATE car_rentals SET end_date = ? WHERE id = ?",
            (end_date.strftime("%Y-%m-%d"), rental_id),
        )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully updated."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."


@tool
def cancel_car_rental(rental_id: int) -> str:
    """Cancel a car rental by its ID."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("UPDATE car_rentals SET booked = 0 WHERE id = ?", (rental_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Car rental {rental_id} successfully cancelled."
    else:
        conn.close()
        return f"No car rental found with ID {rental_id}."
