##We define two core targets for your LangGraph agents: one for structured timelines/events, and one for unstructured knowledge documents.
# What this accomplishes:
# Decouples Engine from DB Backend: Using SQLAlchemy means this exact file works seamlessly whether you back it with a local SQLite file or a production PostgreSQL cluster.

# Separates Modalities: Structured data with granular metadata queries goes to unified_events, while raw articles/web scrapes for RAG injections go to unified_knowledge.
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base

# Initialize the declarative base for ORM mapping
Base = declarative_base()


class UnifiedEvent(Base):
    """Target schema for structured, timeline-based data (e.g., NeoWs, DONKI, EONET)"""

    __tablename__ = "unified_events"

    id = Column(String, primary_key=True)
    source_provider = Column(String, nullable=False)  # e.g., 'nasa', 'spaceflight'
    dataset_id = Column(String, nullable=False)  # e.g., 'neows', 'donki'
    event_timestamp = Column(DateTime, nullable=False, index=True)
    title = Column(String, nullable=False)
    raw_payload = Column(
        JSON, nullable=True
    )  # Preserves full bronze layer payload for auditability
    extracted_metadata = Column(
        JSON, nullable=True
    )  # Flattened, normalized metrics tailored for LangGraph tools


class UnifiedKnowledge(Base):
    """Target schema for unstructured, content-heavy text data (e.g., APOD, HTML markdown)"""

    __tablename__ = "unified_knowledge"

    id = Column(String, primary_key=True)
    source_provider = Column(String, nullable=False)  # e.g., 'nasa'
    dataset_id = Column(String, nullable=False)  # e.g., 'jwst', 'apod'
    title = Column(String, nullable=False)
    content = Column(
        Text, nullable=False
    )  # Plain text/markdown content optimized for LLM context windows
    source_url = Column(String, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True, index=True)


class DatasetFreshness(Base):
    """Tracks the last successful/failed ingestion run per dataset_id.

    One row per dataset_id, upserted after every pipeline run. This is what
    lets you answer "is anything silently stale?" with a query instead of
    grepping GitHub Actions logs.
    """

    __tablename__ = "dataset_freshness"

    dataset_id = Column(String, primary_key=True)  # e.g. 'neows', 'jwst'
    source_provider = Column(String, nullable=False)
    last_ingested_at = Column(DateTime, nullable=False)
    last_status = Column(String, nullable=False)  # 'success' | 'failed'
    records_processed = Column(JSON, nullable=True)  # int, but JSON keeps it flexible
    last_error = Column(Text, nullable=True)
