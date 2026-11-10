from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import VectorStore


class KnowledgeRetriever:
    """Simplified knowledge access layer that reads corpus files from disk."""

    def __init__(self, knowledge_dir: str | Path | None = None, vector_store: VectorStore | None = None) -> None:
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir is not None else settings.knowledge_dir
        self.vector_store = vector_store or VectorStore()

    def load_guidance(self, topic: str | None = None) -> list[str]:
        """Return guidance snippets from a local knowledge directory."""
        files = sorted(self.knowledge_dir.glob("*.md"))
        guidance: list[str] = []
        for file in files:
            content = file.read_text(encoding="utf-8")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            if topic:
                if topic.lower() in file.name.lower() or topic.lower() in " ".join(lines).lower():
                    guidance.extend(lines[:6])
            else:
                guidance.extend(lines[:6])
        return guidance

    def ingest(self) -> list[str]:
        documents = DocumentLoader(self.knowledge_dir).load_documents()
        self.vector_store.ingest_documents(documents)
        return [doc["id"] for doc in documents]

    def search(self, query: str, limit: int = 5) -> list[str]:
        return self.vector_store.query(query_text=query, limit=limit)
