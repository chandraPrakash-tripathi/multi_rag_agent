Step 0 — Orientation (5 min)

README.md (root) — architecture overview, the graph diagram image, and the "Next Steps" section
docker-compose.yml + Dockerfile — see what services exist and how they connect (this tells you vectorizer runs first, customer_support_chat depends on it)

Step 1 — Vectorizer service (data goes in first)
Read this whole service before touching the chat service — nothing in the chat app makes sense without knowing what's in the vector DB.

vectorizer/README.md — overview
vectorizer/app/core/settings.py — config/env vars
vectorizer/app/vectordb/chunkenizer.py — how raw text gets split into chunks
vectorizer/app/embeddings/embedding_generator.py — how chunks become vectors
vectorizer/app/vectordb/vectordb.py — the VectorDB class: connecting to Qdrant, formatting content per collection type, indexing, batching, async processing, and the search method
vectorizer/app/main.py — orchestrates all of the above to build the collections

Step 2 — Customer support chat service (the agent layer)
Now that you know what's retrievable, read the chat app top-down by responsibility, not file order:

customer_support_chat/README.md — overview
customer_support_chat/app/core/settings.py and state.py — config and the shared conversation state schema (read this before graph.py — you need to know what's in state to understand routing)
customer_support_chat/app/services/tools/*.py (flights.py, hotels.py, cars.py, excursions.py, lookup.py) — the actual safe/sensitive tools each assistant calls
customer_support_chat/app/services/assistants/assistant_base.py — the Strategy Pattern base class + CompleteOrEscalate — this is the most important file to understand deeply, everything else inherits from it
customer_support_chat/app/services/assistants/primary_assistant.py — the supervisor/router logic (Chain of Responsibility pattern)
customer_support_chat/app/services/assistants/flight_booking_assistant.py (then car_rental, hotel_booking, excursion — these four are near-identical, so just skim after the first one)
customer_support_chat/app/graph.py — the LangGraph state graph: node definitions, conditional edges, interrupt handling for sensitive tools. This is where everything you read above gets wired together.
customer_support_chat/app/services/vectordb/vectordb.py — the retrieval call the tools make (same pattern as vectorizer's, but this is the read/query side)
customer_support_chat/app/main.py — entry point: the interaction loop, interrupt confirmation, graph visualization

Step 3 — Data

customer_support_chat/data/travel2.sqlite schema (via the image in README) — understand what the underlying travel DB actually contains, since every tool ultimately queries this