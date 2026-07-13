import os
import uuid
from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Import your Silver Layer schema
from data_setup.unified_layer.models import UnifiedKnowledge


class VectorKnowledgeBuilder:
    """ETL Pipeline moving clean text from SQLite into a Qdrant Vector Database."""

    def __init__(self):
        # 1. Relational Database Connection (Silver Layer)
        self.sqlite_url = os.getenv("DATABASE_URL", "sqlite:///unified_layer.db")
        self.engine = create_engine(self.sqlite_url)
        self.Session = sessionmaker(bind=self.engine)

        # 2. Vector Database Connection (Qdrant on Docker)
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant = QdrantClient(url=self.qdrant_url)
        self.collection_name = "unified_knowledge_collection"

        # 3. Embedding Model Initialization
        # all-MiniLM-L6-v2 is highly optimized for RAG.
        # The architecture allows for seamless substitution with specialized transformer models like
        # DistilBERT if your natural language processing applications require different density profiles.
        print("[+] Loading embedding model... (This may take a moment on first run)")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

        # 4. Initialize Qdrant Collection
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        collections = self.qdrant.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            print(f"[+] Creating Qdrant collection: {self.collection_name}")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size, distance=models.Distance.COSINE
                ),
            )

    def fetch_knowledge_documents(self) -> List[UnifiedKnowledge]:
        """Step 8: Fetch parsed, clean text from the unified layer."""
        session = self.Session()
        try:
            # We filter out any accidentally empty content blocks
            docs = (
                session.query(UnifiedKnowledge)
                .filter(UnifiedKnowledge.content != "")
                .all()
            )
            print(f"[+] Retrieved {len(docs)} documents from SQLite.")
            return docs
        finally:
            session.close()

    def chunk_documents(
        self, documents: List[UnifiedKnowledge]
    ) -> List[Dict[str, Any]]:
        """Step 9: Split text into semantic chunks while retaining metadata."""
        # Recursive splitter ensures paragraphs and sentences aren't split in half
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=150, separators=["\n\n", "\n", ".", " ", ""]
        )

        chunked_payloads = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.content)

            for index, chunk_text in enumerate(chunks):
                # Qdrant requires UUIDs or Integers for point IDs.
                # We use uuid5 to deterministically generate an ID based on the doc ID and chunk index.
                # This guarantees idempotency (rerunning the script overwrites rather than duplicates).
                deterministic_id = str(
                    uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.id}_{index}")
                )

                chunked_payloads.append(
                    {
                        "id": deterministic_id,
                        "text": chunk_text,
                        "metadata": {
                            "source_id": doc.id,
                            "provider": doc.source_provider,
                            "dataset": doc.dataset_id,
                            "title": doc.title,
                            "chunk_index": index,
                        },
                    }
                )

        print(
            f"[+] Chunked {len(documents)} documents into {len(chunked_payloads)} total segments."
        )
        return chunked_payloads

    def generate_and_store_embeddings(
        self, chunked_payloads: List[Dict[str, Any]], batch_size: int = 100
    ):
        """Step 10 & 11: Generate vector embeddings and upsert to Qdrant in batches."""
        total_chunks = len(chunked_payloads)

        for i in range(0, total_chunks, batch_size):
            batch = chunked_payloads[i : i + batch_size]

            # Step 10: Vectorize the batch of text strings
            texts = [item["text"] for item in batch]
            embeddings = self.embedding_model.encode(texts).tolist()

            # Formulate Qdrant PointStructs
            points = []
            for item, vector in zip(batch, embeddings):
                # Inject the raw text right into the payload alongside the metadata
                # so the LangGraph agent can read it after the vector search
                payload = item["metadata"]
                payload["page_content"] = item["text"]

                points.append(
                    models.PointStruct(id=item["id"], vector=vector, payload=payload)
                )

            # Step 11: Upsert to the Vector Database
            self.qdrant.upsert(collection_name=self.collection_name, points=points)
            print(
                f"  -> Upserted batch {i} to {min(i + batch_size, total_chunks)} / {total_chunks}"
            )

    def run_pipeline(self):
        """Executes the full Phase 2 architecture."""
        print("=" * 60)
        print("Starting Knowledge Vectorization Pipeline")
        print("=" * 60)

        docs = self.fetch_knowledge_documents()
        if not docs:
            print("[-] No documents found in Silver layer. Exiting.")
            return

        chunks = self.chunk_documents(docs)
        self.generate_and_store_embeddings(chunks)

        print("[✓] Vector knowledge base successfully populated!")


if __name__ == "__main__":
    builder = VectorKnowledgeBuilder()
    builder.run_pipeline()
