from typing import List
from data_setup.unified_layer.models import UnifiedKnowledge
from agent.app.core.repository.base import BaseRepository


class NewsRepository(BaseRepository):
    def get_latest(self, limit: int = 10) -> List[dict]:
        with self.get_session() as session:
            rows = (
                session.query(UnifiedKnowledge)
                .filter(UnifiedKnowledge.dataset_id == "spaceflight_news")
                .order_by(UnifiedKnowledge.published_at.desc())
                .limit(limit)
                .all()
            )
        return [self._knowledge_to_dict(r) for r in rows]
