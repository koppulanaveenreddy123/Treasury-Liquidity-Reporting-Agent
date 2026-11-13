from __future__ import annotations

from app.rag.chunker import Chunker
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import VectorStore


class IngestionService:
    """Load knowledge documents into a vector store."""

    def __init__(self, knowledge_dir: str | None = None) -> None:
        self.loader = DocumentLoader(knowledge_dir)
        self.chunker = Chunker()
        self.vector_store = VectorStore()

    def ingest(self) -> None:
        """Ingest knowledge content into ChromaDB."""
        documents = self.loader.load_documents()
        chunks: list[dict[str, str]] = []
        for doc in documents:
            for index, chunk in enumerate(self.chunker.chunk(doc["text"])):
                chunks.append({"id": f"{doc['id']}-{index}", "text": chunk})
        self.vector_store.add_documents(chunks)
