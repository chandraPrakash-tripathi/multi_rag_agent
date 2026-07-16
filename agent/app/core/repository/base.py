from contextlib import contextmanager
from data_setup.unified_layer.database import SessionLocal


class BaseRepository:
    """Shared session lifecycle + dict-conversion logic for all repos.
    Every method opens its own session, queries, converts to plain dicts,
    and closes before returning — no ORM instance ever leaks past this layer.
    """

    @contextmanager
    def get_session(self):
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @staticmethod
    def _event_to_dict(event) -> dict:
        """Flattens extracted_metadata to top level. raw_payload is dropped —
        it's the full bronze audit blob and would blow up tool-call token cost."""
        base = {
            "id": event.id,
            "title": event.title,
            "event_timestamp": (
                event.event_timestamp.isoformat() if event.event_timestamp else None
            ),
            "source_provider": event.source_provider,
            "dataset_id": event.dataset_id,
        }
        base.update(event.extracted_metadata or {})
        return base

    @staticmethod
    def _knowledge_to_dict(record) -> dict:
        return {
            "id": record.id,
            "title": record.title,
            "content": record.content,
            "source_url": record.source_url,
            "source_provider": record.source_provider,
            "dataset_id": record.dataset_id,
            "published_at": (
                record.published_at.isoformat()
                if getattr(record, "published_at", None)
                else None
            ),
        }
