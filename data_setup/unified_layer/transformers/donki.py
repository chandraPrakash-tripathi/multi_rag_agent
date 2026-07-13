# Array Normalization: The DONKI API natively returns a JSON list instead of a nested dictionary (unlike NeoWs).
#  The transformer immediately normalizes the input loop to handle this safely.

# Context Preservation: By storing the massive text block of messageBody inside the raw_payload
# JSON column but intentionally omitting it from extracted_metadata, your SQLite queries stay extremely fast and token-efficient.
import json
from datetime import datetime
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedEvent
from data_setup.unified_layer.transformers.base import BaseTransformer


class DonkiTransformer(BaseTransformer):
    """Transformer for NASA Space Weather Database Of Notifications (DONKI) JSON payloads."""

    def transform(self, file_path: Path) -> List[UnifiedEvent]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []

        # DONKI API typically returns a direct list of notification objects
        if not isinstance(raw_data, list):
            raw_data = [raw_data]

        for notification in raw_data:
            # Extract standard fields (using dict.get() for safety)
            message_id = notification.get("messageID")
            message_type = notification.get("messageType", "UNKNOWN_EVENT")
            issue_time_str = notification.get("messageIssueTime")

            if not message_id or not issue_time_str:
                continue  # Skip invalid or severely malformed entries

            try:
                # DONKI timestamps are typically ISO-8601 formatted with a "Z"
                event_date = datetime.fromisoformat(
                    issue_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                continue

            # We strip the bulky text body out of the metrics to keep the LangGraph tool footprint small
            # The full message body remains available in the raw_payload column if needed
            metrics = {
                "message_type": message_type,
                "message_url": notification.get("messageURL"),
            }

            # Construct unified event mapping
            record = UnifiedEvent(
                id=f"donki_{message_id}",
                source_provider="nasa",
                dataset_id="donki",
                event_timestamp=event_date,
                title=f"Space Weather Notification: {message_type}",
                raw_payload=notification,
                extracted_metadata=metrics,
            )
            unified_records.append(record)

        return unified_records
