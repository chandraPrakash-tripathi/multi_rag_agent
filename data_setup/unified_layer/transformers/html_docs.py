# Noise Decomposition: It explicitly searches for and deletes structural web pollution (such as scripts, stylesheets, sidebars, headers, and footers)
# that would otherwise inflate the LangGraph agent's context token counts.

# Structural Parsing: It identifies headings, lists, and main body tags, merging them with clean double-newline breaks to maintain structural readability
# when passed to the LLM.

# Dynamic Metadata Tracking: It traces the local file architecture's relative folder layout to figure out the provider and dataset_id implicitly.

from pathlib import Path
from typing import List
from bs4 import BeautifulSoup
from data_setup.unified_layer.models import UnifiedKnowledge
from data_setup.unified_layer.transformers.base import BaseTransformer


class HtmlDocsTransformer(BaseTransformer):
    """Transformer for parsing raw unstructured HTML documentation pages into clean plain text markdown segments."""

    def transform(self, file_path: Path) -> List[UnifiedKnowledge]:
        # Read the raw binary or text content from disk
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        # Initialize BeautifulSoup to parse the layout tree
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip script, style, and navigation noise tags that pollute context windows
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()

        # Extract the page title or fall back to the filename stem if missing
        title_tag = soup.find("title") or soup.find("h1")
        extracted_title = (
            title_tag.get_text(strip=True) if title_tag else file_path.stem
        )

        # Extract structural paragraph texts, stripping out whitespace bloat
        paragraphs = []
        for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        # Combine text segments into a single unified body block
        clean_content = "\n\n".join(paragraphs)

        # Skip files that have absolutely no meaningful textual information inside
        if not clean_content.strip():
            return []

        # Derive provider and dataset contexts safely from the directory hierarchy path
        # Architecture expectation: data_unstr/{provider}/{dataset_id}/{filename}
        parts = file_path.parts
        provider = parts[-3] if len(parts) >= 3 else "unknown"
        dataset_id = parts[-2] if len(parts) >= 2 else "html_doc"

        # Unique ID generated via combination of the file identifier and dataset metadata
        record_id = f"{dataset_id}_latest"

        record = UnifiedKnowledge(
            id=record_id,
            source_provider=provider,
            dataset_id=dataset_id,
            title=extracted_title,
            content=clean_content,
            source_url=None,  # Can be populated at orchestration level via runtime lookup if desired
        )

        return [record]
