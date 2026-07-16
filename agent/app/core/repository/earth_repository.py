from typing import List, Optional
from data_setup.unified_layer.models import UnifiedEvent
from agent.app.core.repository.base import BaseRepository
from datetime import datetime, timedelta

DEFAULT_LOOKBACK_DAYS = 30


class EarthEventsRepository(BaseRepository):
    def get_active_events(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[dict]:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        with self.get_session() as session:
            rows = (
                session.query(UnifiedEvent)
                .filter(
                    UnifiedEvent.dataset_id == "eonet",
                    UnifiedEvent.event_timestamp >= cutoff,
                )
                .order_by(UnifiedEvent.event_timestamp.desc())
                .all()
            )
        records = [
            self._event_to_dict(r)
            for r in rows
            if (r.extracted_metadata or {}).get("status") == "open"
        ]
        if category:
            records = [r for r in records if r.get("category") == category]
        return records[:limit]
