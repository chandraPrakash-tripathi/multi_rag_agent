from typing import List, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os


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
        self,
        query: str,
        limit: int,
        dataset_filter: Optional[str] = None,
        exclude_datasets: Optional[List[str]] = None,
    ) -> List[dict]:
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

        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=limit,
        )

        return [
            {
                "text": hit.payload.get("page_content"),
                "title": hit.payload.get("title"),
                "source_id": hit.payload.get("source_id"),
                "dataset": hit.payload.get("dataset"),
                "score": hit.score,
            }
            for hit in results
        ]

    def search_scientific_knowledge(self, query: str, limit: int = 3) -> List[dict]:
        # Excludes news and (optionally) apod so science queries don't get diluted by unrelated chunks
        return self._search(query, limit, exclude_datasets=["spaceflight_news"])

    def search_news_archives(self, query: str, limit: int = 5) -> List[dict]:
        return self._search(query, limit, dataset_filter="spaceflight_news")
