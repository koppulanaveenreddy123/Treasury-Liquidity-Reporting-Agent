from __future__ import annotations

from pathlib import Path


class DocumentLoader:
    """Load markdown knowledge documents for ingestion into ChromaDB."""

    def __init__(self, knowledge_dir: str | Path | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir is not None else Path("app/knowledge")

    def load_documents(self) -> list[dict[str, str]]:
        """Return all markdown documents as text blocks."""
        documents: list[dict[str, str]] = []
        for file_path in sorted(self.knowledge_dir.glob("*.md")):
            text = file_path.read_text(encoding="utf-8")
            documents.append({
                "id": file_path.stem,
                "text": text,
                "document_name": file_path.name,
                "document_version": "v1",
                "source_type": "synthetic_treasury_guidance",
            })
        return documents
