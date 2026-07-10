import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from agent.app.core.settings import get_settings
from agent.app.services.utils import get_qdrant_client
from agent.app.services.vectordb.chunkenizer import recursive_character_splitting
from agent.app.services.embeddings.embedding_generator import generate_embedding
from agent.app.core.logger import logger

settings = get_settings()

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5


class VectorDB:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.client = get_qdrant_client()
        self.create_collection()

    def create_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created new collection: {self.collection_name}")
        else:
            logger.info(f"Collection {self.collection_name} already exists")

    def upsert_vector(self, doc_id, chunk_text, embedding, url, chunk_index):
        chunk_id = str(uuid.uuid4())
        payload = {
            "url": url,
            "document_id": str(doc_id),
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
        }
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(id=chunk_id, vector=embedding, payload=payload)],
        )

    def create_embeddings(self, docs):
        for doc_id, content, url in docs:
            if content is None:
                logger.warning(f"Skipping doc_id {doc_id} because content is None")
                continue

            chunks = recursive_character_splitting(content)
            if not chunks:
                continue

            try:
                embeddings = generate_embedding(
                    chunks
                )  # batched, no per-chunk model calls
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    self.upsert_vector(doc_id, chunk, embedding, url, i)
                logger.info(f"Indexed {len(chunks)} chunks for doc_id: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to embed/store doc_id {doc_id}: {str(e)}")

        logger.info("Completed generating embeddings for all documents")

    def search(self, query, k=3):
        query_embedding = generate_embedding(query, is_query=True)
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k,
            with_payload=True,
        )
        return search_result
