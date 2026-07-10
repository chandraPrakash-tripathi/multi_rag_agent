import sqlite3
import uuid
import re
import asyncio
import aiohttp
from tqdm.asyncio import tqdm_asyncio
from more_itertools import chunked

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from vectorizer.app.core.settings import get_settings
from vectorizer.app.core.logger import logger
from .chunknizer import recursive_character_splitting
from vectorizer.app.embeddings.embedding_generator import generate_embedding

settings = get_settings()

# Gemini's text-embedding-004 outputs 768-dim vectors (not OpenAI's 1536)
EMBEDDING_DIM = 384


class VectorDB:
    def __init__(self, table_name, collection_name, create_collection=False):
        self.table_name = table_name
        self.collection_name = collection_name
        self.connect_to_qdrant()
        if create_collection:
            self.create_or_clear_collection()

    def connect_to_qdrant(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        logger.info("Connected to Qdrant")

    def create_or_clear_collection(self):
        if self.client.collection_exists(self.collection_name):
            logger.info(
                f"Collection {self.collection_name} already exists. Recreating it."
            )
            self.client.delete_collection(collection_name=self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {self.collection_name}")

    def format_content(self, data, collection_name):
        if collection_name == "car_rentals_collection":
            booking_status = "booked" if data["booked"] else "not booked"
            return (
                f"Car rental: {data['name']}, located at: {data['location']}, price tier: {data['price_tier']}. "
                + f"Rental period starts on {data['start_date']} and ends on {data['end_date']}. "
                + f"Currently, the rental is: {booking_status}."
            )

        elif collection_name == "excursions_collection":
            booking_status = "booked" if data["booked"] else "not booked"
            return (
                f"Excursion: {data['name']} at {data['location']}. "
                + f"Additional details: {data['details']}. "
                + f"Currently, the excursion is {booking_status}. "
                + f"Keywords: {data['keywords']}."
            )

        elif collection_name == "flights_collection":
            return (
                f"Flight {data['flight_no']} from {data['departure_airport']} to {data['arrival_airport']} "
                + f"was scheduled to depart at {data['scheduled_departure']} and arrive at {data['scheduled_arrival']}. "
                + f"The actual departure was at {data['actual_departure']} and the actual arrival was at {data['actual_arrival']}. "
                + f"Currently, the flight status is '{data['status']}' and it was operated with aircraft code {data['aircraft_code']}."
            )

        elif collection_name == "hotels_collection":
            booking_status = "booked" if data["booked"] else "not booked"
            return (
                f"Hotel {data['name']} located in {data['location']} is categorized as {data['price_tier']} tier. "
                + f"The check-in date is {data['checkin_date']} and the check-out date is {data['checkout_date']}. "
                + f"Currently, the booked status is: {booking_status}."
            )

        elif collection_name == "faq_collection":
            return data["page_content"]
        else:
            return str(data)

    async def generate_embedding_async(self, content):
        return await asyncio.to_thread(generate_embedding, content)

    async def process_chunk(self, chunk, metadata):
        embedding = await self.generate_embedding_async(chunk)
        return PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"content": chunk, **metadata},
        )

    async def create_embeddings_async(self):
        if self.table_name == "faq":
            await self.index_faq_docs()
        else:
            await self.index_regular_docs()

    async def index_regular_docs(self):
        db_connection = sqlite3.connect(settings.SQLITE_DB_PATH)
        cursor = db_connection.cursor()
        cursor.execute(f"SELECT * FROM {self.table_name}")
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        db_connection.close()

        if not rows:
            logger.warning(f"No data found in table {self.table_name}")
            return

        data = [dict(zip(column_names, row)) for row in rows]
        chunks = [self.format_content(item, self.collection_name) for item in data]
        chunks = [
            chunk
            for item in chunks
            for chunk in recursive_character_splitting(item)
            if chunk
        ]

        if not chunks:
            logger.warning(f"No valid chunks generated for {self.collection_name}")
            return

        batch_size = 64  # Gemini free-tier rate limits are tighter than OpenAI's
        delay = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            tasks = [
                self.process_chunk(chunk, {"source_table": self.table_name})
                for chunk in batch
            ]

            points = []
            for task in tqdm_asyncio.as_completed(
                tasks,
                desc=f"Generating embeddings for {self.collection_name} (batch {i//batch_size + 1})",
                total=len(tasks),
            ):
                try:
                    point = await task
                    if point is not None:
                        points.append(point)
                except Exception as e:
                    logger.error(f"Error processing chunk: {str(e)}")

            if points:
                self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info(
                    f"Indexed {len(points)} documents into {self.collection_name} (batch {i//batch_size + 1})"
                )

            if i + batch_size < len(chunks):
                logger.info(f"Waiting {delay}s before next batch...")
                await asyncio.sleep(delay)

        logger.info(
            f"Finished indexing. Total chunks indexed into {self.collection_name}: {len(chunks)}"
        )

    async def index_faq_docs(self):
        faq_url = (
            "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(faq_url) as response:
                faq_text = await response.text()

        docs = [
            {"page_content": txt.strip()}
            for txt in re.split(r"(?=\n##)", faq_text)
            if txt.strip()
        ]

        tasks = [
            self.process_chunk(doc["page_content"], {"type": "faq"}) for doc in docs
        ]
        points = await tqdm_asyncio.gather(
            *tasks, desc="Generating embeddings for FAQ documents"
        )

        if points:
            for batch in chunked(points, 20):
                self.client.upsert(collection_name=self.collection_name, points=batch)
            logger.info(
                f"Indexed {len(points)} FAQ documents into {self.collection_name}."
            )
        else:
            logger.warning("No FAQ documents were successfully embedded and indexed.")

    def create_embeddings(self):
        asyncio.run(self.create_embeddings_async())

    def search(self, query, limit=2, with_payload=True):
        query_vector = generate_embedding(query)
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=with_payload,
        )
        return search_result


if __name__ == "__main__":
    vectordb = VectorDB("example_table", "example_collection")
    vectordb.create_embeddings()
