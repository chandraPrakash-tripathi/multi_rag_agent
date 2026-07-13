# What this accomplishes:
# Failsafe Metrics Casting: Deeply nested JSON elements (like diameters and close-approach array values) are parsed and cast to proper types,
# preventing the LLM from executing mathematical parsing.

# Deterministic IDs: The internal database ID is prefixed explicitly (neows_{id}), ensuring that subsequent ingestions merge updates rather than creating
# duplicate row conflicts.
import json
from datetime import datetime
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedEvent
from data_setup.unified_layer.transformers.base import BaseTransformer


class NeoWsTransformer(BaseTransformer):
    """Transformer for NASA Near Earth Object Web Service (NeoWs) structured JSON payloads."""

    def transform(self, file_path: Path) -> List[UnifiedEvent]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []
        near_earth_objects = raw_data.get("near_earth_objects", {})

        # NeoWs groups asteroids by dates (e.g., "2026-07-11")
        for date_str, asteroids in near_earth_objects.items():
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

            for asteroid in asteroids:
                # Extract primary close approach details safely
                close_approach_list = asteroid.get("close_approach_data", [])
                close_approach = close_approach_list[0] if close_approach_list else {}

                miss_distance = close_approach.get("miss_distance", {}).get(
                    "kilometers"
                )
                velocity = close_approach.get("relative_velocity", {}).get(
                    "kilometers_per_hour"
                )

                # Standardize complex metrics into a flat, clean dict for LLM tools
                metrics = {
                    "estimated_diameter_km_max": asteroid.get("estimated_diameter", {})
                    .get("kilometers", {})
                    .get("estimated_diameter_max"),
                    "miss_distance_km": float(miss_distance) if miss_distance else None,
                    "relative_velocity_kph": float(velocity) if velocity else None,
                    "is_potentially_hazardous": asteroid.get(
                        "is_potentially_hazardous_asteroid", False
                    ),
                }

                # Construct unified event mapping
                record = UnifiedEvent(
                    id=f"neows_{asteroid.get('id')}",
                    source_provider="nasa",
                    dataset_id="neows",
                    event_timestamp=event_date,
                    title=f"Asteroid Close Approach: {asteroid.get('name', 'Unknown')}",
                    raw_payload=asteroid,  # Retains full nested history for fallback auditing
                    extracted_metadata=metrics,
                )
                unified_records.append(record)

        return unified_records
