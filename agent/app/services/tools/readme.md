| Tool File           | Purpose                                 | What it is used for                                                                                                                                                                                               |
| ------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`cars.py`**       | Manages car rental operations           | Searches car rentals using **Qdrant** and books, updates, or cancels rentals in **SQLite**.                                                                                                                       |
| **`hotels.py`**     | Manages hotel operations                | Searches hotels using **Qdrant** and books, updates, or cancels hotel reservations in **SQLite**.                                                                                                                 |
| **`excursions.py`** | Manages excursion/trip recommendations  | Searches excursions using **Qdrant** and books, updates, or cancels excursions in **SQLite**.                                                                                                                     |
| **`lookup.py`**     | Provides company knowledge and policies | Searches FAQs and company policies from **Qdrant** to answer policy questions or verify whether an action (e.g., cancellation or flight change) is allowed. It is **read-only** and does not modify the database. |


Overall pattern
cars.py, hotels.py, and excursions.py are action tools:
Retrieve relevant options from Qdrant.
Perform booking-related updates in SQLite.
lookup.py is a knowledge tool:
Retrieves company policies and FAQs from Qdrant.
Never performs database updates.

In short:

Cars, Hotels, Excursions → Search + CRUD (book/update/cancel) operations.
Lookup → Policy/FAQ retrieval and validation before executing actions.

for flights.py
flights.py is built around authenticated user-specific bookings, enforcing ownership checks through RunnableConfig and relational database queries before allowing any updates or cancellations, making it the most secure and realistic module in the project.

| Feature                                     | Cars/Hotels/Excursions | Flights |
| ------------------------------------------- | ---------------------- | ------- |
| Semantic search                             | ✅                      | ✅       |
| Book/Update/Cancel                          | ✅                      | ✅       |
| Uses SQLite                                 | ✅                      | ✅       |
| Uses Qdrant                                 | ✅                      | ✅       |
| **Requires logged-in user**                 | ❌                      | ✅       |
| **Verifies ownership before update/cancel** | ❌                      | ✅       |
| **Joins multiple tables**                   | ❌                      | ✅       |
