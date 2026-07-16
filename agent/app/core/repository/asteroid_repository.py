from datetime import datetime, timedelta
from typing import List
from data_setup.unified_layer.models import UnifiedEvent
from agent.app.core.repository.base import BaseRepository

DEFAULT_LOOKBACK_DAYS = 30


class AsteroidRepository(BaseRepository):
    def get_hazardous(self, start_date: datetime, end_date: datetime) -> List[dict]:
        with self.get_session() as session:
            rows = (
                session.query(UnifiedEvent)
                .filter(
                    UnifiedEvent.dataset_id == "neows",
                    UnifiedEvent.event_timestamp.between(start_date, end_date),
                )
                .all()
            )
        return [
            self._event_to_dict(r)
            for r in rows
            if (r.extracted_metadata or {}).get("is_potentially_hazardous") is True
        ]

    def get_closest_approaches(
        self,
        limit: int = 10,
        sort_by: str = "distance",
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[dict]:
        if sort_by not in ("distance", "speed"):
            raise ValueError(f"sort_by must be 'distance' or 'speed', got {sort_by!r}")

        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        with self.get_session() as session:
            rows = (
                session.query(UnifiedEvent)
                .filter(
                    UnifiedEvent.dataset_id == "neows",
                    UnifiedEvent.event_timestamp >= cutoff,
                )
                .all()
            )

        records = [self._event_to_dict(r) for r in rows]
        if sort_by == "distance":
            records.sort(
                key=lambda r: (
                    r.get("miss_distance_km")
                    if r.get("miss_distance_km") is not None
                    else float("inf")
                )
            )
        else:
            records.sort(
                key=lambda r: r.get("relative_velocity_kph") or 0, reverse=True
            )

        return records[:limit]
