import os
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Fix 6: Environment-driven vector threshold
VECTOR_SEARCH_THRESHOLD = float(os.getenv("VECTOR_SEARCH_THRESHOLD", "0.3"))


class KnowledgeRepository:
    """Wraps Qdrant vector search. Structurally different from the SQL repos —
    no SQLAlchemy session — but exposes the same 'returns list of dicts' contract."""

    _embedding_model = (
        None  # loaded once, shared across instances — expensive to init per call
    )

    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection_name = "unified_knowledge_collection"
        if KnowledgeRepository._embedding_model is None:
            KnowledgeRepository._embedding_model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

    def _search(
        self, query: str, limit: int, dataset_filter=None, exclude_datasets=None
    ) -> list[dict]:
        query_vector = KnowledgeRepository._embedding_model.encode(query).tolist()

        must_conditions = []
        must_not_conditions = []

        if dataset_filter:
            must_conditions.append(
                models.FieldCondition(
                    key="dataset", match=models.MatchValue(value=dataset_filter)
                )
            )
        if exclude_datasets:
            must_not_conditions = [
                models.FieldCondition(key="dataset", match=models.MatchValue(value=ds))
                for ds in exclude_datasets
            ]

        qdrant_filter = None
        if must_conditions or must_not_conditions:
            qdrant_filter = models.Filter(
                must=must_conditions or None, must_not=must_not_conditions or None
            )

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,  # note: 'query', not 'query_vector' — different param name
            query_filter=qdrant_filter,
            limit=limit,
            score_threshold=VECTOR_SEARCH_THRESHOLD,  # <-- Fix 6: enforce relevance threshold
        )

        results = [
            {
                "text": point.payload.get("page_content"),
                "title": point.payload.get("title"),
                "source_id": point.payload.get("source_id"),
                "dataset": point.payload.get("dataset"),
                "score": point.score,
            }
            for point in response.points  # query_points wraps results in a .points list
        ]

        # Fix 6: Log when no results meet the threshold
        if not results:
            logger.warning(
                f"Vector search for '{query}' returned 0 results (threshold: {VECTOR_SEARCH_THRESHOLD})."
            )

        return results

    def search_scientific_knowledge(self, query: str, limit: int = 3) -> List[dict]:
        # Excludes news and (optionally) apod so science queries don't get diluted by unrelated chunks
        return self._search(query, limit, exclude_datasets=["spaceflight_news"])

    def search_news_archives(self, query: str, limit: int = 5) -> List[dict]:
        return self._search(query, limit, dataset_filter="spaceflight_news")
