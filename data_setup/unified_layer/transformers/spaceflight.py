# Target Extraction: It isolates the results payload envelope signature specific to the Spaceflight News API v4 structure.Knowledge Standardizing:
# It handles semantic fallback logic (summary $\rightarrow$ title) to guarantee the content block is never empty for your downstream LangGraph retrieval tools.
# Traceability Mapping: It explicitly names the source_provider as spaceflight to keep it cleanly segmented away from the NASA datasets inside the same unified_knowledge table.
import json
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedKnowledge
from data_setup.unified_layer.transformers.base import BaseTransformer


class SpaceflightTransformer(BaseTransformer):
    """Transformer for Spaceflight News API v4 JSON articles payloads."""

    def transform(self, file_path: Path) -> List[UnifiedKnowledge]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []

        # Spaceflight News API v4 wraps its article list inside the 'results' key
        articles = raw_data.get("results", [])

        # Fallback in case the raw data is already a direct list of articles
        if not isinstance(articles, list) and isinstance(raw_data, list):
            articles = raw_data

        for article in articles:
            article_id = article.get("id")
            title = article.get("title")
            # We utilize the summary or fallback to title if summary is missing
            summary = article.get("summary") or article.get("title", "")
            url = article.get("url")

            if not article_id or not title:
                continue

            record = UnifiedKnowledge(
                id=f"spaceflight_{article_id}",
                source_provider="spaceflight",
                dataset_id="spaceflight_news",
                title=title,
                content=summary,
                source_url=url,
            )
            unified_records.append(record)

        return unified_records
