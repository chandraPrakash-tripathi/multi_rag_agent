import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Import your Silver Layer schema
from data_setup.unified_layer.models import UnifiedEvent


class DataRepository:
    """Unified Data Access Layer for LangGraph Agents."""

    def __init__(self):
        # 1. Relational Database Connection (SQLite -> Easy swap to PostgreSQL later)
        self.sqlite_url = os.getenv("DATABASE_URL", "sqlite:///unified_layer.db")
        self.engine = create_engine(self.sqlite_url)
        self.Session = sessionmaker(bind=self.engine)

        # 2. Vector Database Connection (Qdrant)
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant = QdrantClient(url=self.qdrant_url)
        self.collection_name = "unified_knowledge_collection"

        # 3. Embedding Model (For on-the-fly query vectorization)
        print("[+] Initializing DataRepository and loading model...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def get_events(
        self,
        dataset_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Fetch structured timeline events from the SQL database with granular filtering.
        """
        session = self.Session()
        try:
            query = session.query(UnifiedEvent)

            # Filter 1: Dataset Boundary (e.g., 'eonet', 'donki')
            if dataset_id:
                query = query.filter(UnifiedEvent.dataset_id == dataset_id)

            # Filter 2: Time Window (e.g., '2026-07-01' to '2026-07-14')
            if start_date:
                # Assuming incoming format is ISO 8601 string like '2026-07-01T00:00:00'
                dt_start = datetime.fromisoformat(start_date.replace("Z", ""))
                query = query.filter(UnifiedEvent.event_timestamp >= dt_start)

            if end_date:
                dt_end = datetime.fromisoformat(end_date.replace("Z", ""))
                query = query.filter(UnifiedEvent.event_timestamp <= dt_end)

            # Filter 3: Semantic/Keyword filtering in structured data (e.g., "CME" or "Wildfire")
            if keyword:
                search_term = f"%{keyword}%"
                query = query.filter(
                    or_(
                        UnifiedEvent.title.ilike(search_term),
                        UnifiedEvent.description.ilike(search_term),
                    )
                )

            # Order by most recent events
            events = (
                query.order_by(UnifiedEvent.event_timestamp.desc()).limit(limit).all()
            )

            return [
                {
                    "title": e.title,
                    "timestamp": (
                        e.event_timestamp.isoformat() if e.event_timestamp else None
                    ),
                    "description": e.description,
                    "dataset": e.dataset_id,
                }
                for e in events
            ]
        finally:
            session.close()

    def search_knowledge(
        self, query_text: str, dataset_filter: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search, optionally filtered by dataset metadata (Hybrid)."""
        query_vector = self.embedding_model.encode(query_text).tolist()

        query_filter = None
        if dataset_filter:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="dataset", match=models.MatchValue(value=dataset_filter)
                    )
                ]
            )

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        results = []
        for point in response.points:
            results.append(
                {
                    "score": point.score,
                    "title": point.payload.get("title", "Unknown Document"),
                    "dataset": point.payload.get("dataset", "Unknown"),
                    "content": point.payload.get("page_content", ""),
                }
            )

        return results
