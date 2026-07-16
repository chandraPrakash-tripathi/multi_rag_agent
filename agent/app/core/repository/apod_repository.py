from typing import Optional
from data_setup.unified_layer.models import UnifiedKnowledge
from agent.app.core.repository.base import BaseRepository


class ApodRepository(BaseRepository):
    def get_by_date(self, date: str) -> Optional[dict]:
        """date format: 'YYYY-MM-DD' — matches the transformer's id scheme."""
        record_id = f"apod_{date}"
        with self.get_session() as session:
            record = session.get(UnifiedKnowledge, record_id)
        return self._knowledge_to_dict(record) if record else None
