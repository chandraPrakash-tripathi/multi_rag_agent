import json
from datetime import datetime
from pathlib import Path
from typing import List
from data_setup.unified_layer.models import UnifiedKnowledge
from data_setup.unified_layer.transformers.base import BaseTransformer


class SpaceflightTransformer(BaseTransformer):
    def transform(self, file_path: Path) -> List[UnifiedKnowledge]:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        unified_records = []
        articles = raw_data.get("results", [])
        if not isinstance(articles, list) and isinstance(raw_data, list):
            articles = raw_data

        for article in articles:
            article_id = article.get("id")
            title = article.get("title")
            summary = article.get("summary") or article.get("title", "")
            url = article.get("url")

            if not article_id or not title:
                continue

            # NEW — parse the API's real publish timestamp
            published_at_str = article.get("published_at")
            published_at = None
            if published_at_str:
                try:
                    published_at = datetime.fromisoformat(
                        published_at_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    published_at = None

            record = UnifiedKnowledge(
                id=f"spaceflight_{article_id}",
                source_provider="spaceflight",
                dataset_id="spaceflight_news",
                title=title,
                content=summary,
                source_url=url,
                published_at=published_at,
            )
            unified_records.append(record)

        return unified_records
