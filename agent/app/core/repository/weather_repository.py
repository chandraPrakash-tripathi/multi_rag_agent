from typing import List, Optional
from data_setup.unified_layer.models import UnifiedEvent
from agent.app.core.repository.base import BaseRepository
from datetime import datetime, timedelta

DEFAULT_LOOKBACK_DAYS = 30


class WeatherRepository(BaseRepository):
    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 10,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[dict]:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        with self.get_session() as session:
            rows = (
                session.query(UnifiedEvent)
                .filter(
                    UnifiedEvent.dataset_id == "donki",
                    UnifiedEvent.event_timestamp >= cutoff,
                )
                .order_by(UnifiedEvent.event_timestamp.desc())
                .all()
            )
        records = [self._event_to_dict(r) for r in rows]
        if event_type:
            records = [r for r in records if r.get("message_type") == event_type]
        return records[:limit]
