# Model Shift: This is the first adapter to utilize the UnifiedKnowledge schema, pivoting from time-series metrics to unstructured text indexing.Payload Normalization:
# It safely handles varying response structures. It normalizes single JSON objects or {items: [...]} wrapped arrays into a standard iterable sequence.
# Semantic Targeting: It isolates the explanation paragraph as the primary text content.
# It explicitly discards entries without explanations to maintain a high-quality knowledge base for the LangGraph agent.
# Deterministic ID Generation: It leverages the strict YYYY-MM-DD date field as the unique identifier to guarantee idempotency during database merges.
import json
from datetime import datetime
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedKnowledge
from data_setup.unified_layer.transformers.base import BaseTransformer


class ApodTransformer(BaseTransformer):
    """Transformer for NASA Astronomy Picture of the Day (APOD) JSON payloads."""

    def transform(self, file_path: Path) -> List[UnifiedKnowledge]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []

        # APOD returns a single object when querying by a specific date.
        # When queried with a date range, it can wrap the payload in an 'items' array.
        if isinstance(raw_data, dict):
            if "items" in raw_data:
                raw_data = raw_data["items"]
            else:
                raw_data = [raw_data]

        for item in raw_data:
            date_str = item.get("date")
            title = item.get("title", "Unknown APOD")
            explanation = item.get("explanation")

            # If the text explanation is missing, it holds no value for the knowledge base.
            if not explanation or not date_str:
                continue

            # APOD dates act as perfect unique identifiers.
            record_id = f"apod_{date_str}"

            record = UnifiedKnowledge(
                id=record_id,
                source_provider="nasa",
                dataset_id="apod",
                title=title,
                content=explanation,
                # Fallback to standard URL if high-definition URL is missing.
                source_url=item.get("hdurl") or item.get("url"),
            )
            unified_records.append(record)

        return unified_records
