# Geometry Flattening: EONET tracks events over time, generating massive lists of polygon coordinates.
# This transformer safely strips out the heavy GIS plotting data, isolating only the primary timeline and scalar magnitudes (like storm wind speeds)
# for the LangGraph agent tool.  Status Tracking: The logic instantly checks the closed field, mapping the event strictly as "open" (ongoing) or "closed".
import json
from datetime import datetime
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedEvent
from data_setup.unified_layer.transformers.base import BaseTransformer


class EonetTransformer(BaseTransformer):
    """Transformer for NASA Earth Observatory Natural Event Tracker (EONET) v3 JSON payloads."""

    def transform(self, file_path: Path) -> List[UnifiedEvent]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []
        events_list = raw_data.get("events", [])

        for event in events_list:
            event_id = event.get("id")
            title = event.get("title", "Unknown Earth Event")

            # EONET categorizes events (e.g., Wildfires, Severe Storms)
            categories = event.get("categories", [])
            primary_category = (
                categories[0].get("title") if categories else "Uncategorized"
            )

            # Geometries contain the timestamps and locations of the event.
            # An event might span multiple days (like a wildfire), so we grab the first logged date.
            geometries = event.get("geometry", [])
            if not geometries:
                continue

            first_geometry = geometries[0]
            date_str = first_geometry.get("date")

            if not date_str:
                continue

            try:
                # EONET v3 dates are typically ISO-8601 formatted with a 'Z'
                event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            # Extract metrics, dropping the massive coordinate arrays to save LLM tokens
            metrics = {
                "category": primary_category,
                "status": "closed" if event.get("closed") else "open",
                "magnitude_value": first_geometry.get("magnitudeValue"),
                "magnitude_unit": first_geometry.get("magnitudeUnit"),
            }

            # Construct unified event mapping
            record = UnifiedEvent(
                id=f"eonet_{event_id}",
                source_provider="nasa",
                dataset_id="eonet",
                event_timestamp=event_date,
                title=f"Earth Event: {title}",
                raw_payload=event,
                extracted_metadata=metrics,
            )
            unified_records.append(record)

        return unified_records
