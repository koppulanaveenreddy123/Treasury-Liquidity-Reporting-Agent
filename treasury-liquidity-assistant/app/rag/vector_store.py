from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import settings
from app.rag.embedding_service import EmbeddingService

try:
    import chromadb
except ModuleNotFoundError:  # pragma: no cover - fallback for lightweight environments
    chromadb = None


class _InMemoryCollection:
    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []

    def upsert(self, *, ids: list[str], documents: list[str], metadatas: list[dict[str, str]]) -> None:
        entries = {entry["id"]: entry for entry in self._documents}
        for doc_id, document, metadata in zip(ids, documents, metadatas, strict=False):
            entries[doc_id] = {"id": doc_id, "document": document, "metadata": metadata}
        self._documents = list(entries.values())

    def query(self, *, query_texts: list[str], n_results: int) -> dict[str, Any]:
        query = (query_texts[0] if query_texts else "").lower()
        matches: list[str] = []
        for entry in self._documents:
            text = (entry["document"] or "").lower()
            if query in text or (not query and entry["document"]):
                matches.append(entry["document"])
            if len(matches) >= n_results:
                break
        return {"documents": [matches]}

    def count(self) -> int:
        return len(self._documents)


_fallback_collections: dict[str, dict[str, _InMemoryCollection]] = {}


class _InMemoryClient:
    def __init__(self, path: Path) -> None:
        self._collections = _fallback_collections.setdefault(str(path.resolve()), {})

    def get_or_create_collection(self, *, name: str) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection()
        return self._collections[name]


class VectorStore:
    """Public Chroma vector store for synthetic Treasury guidance only."""

    def __init__(self, collection_name: str = "treasury_guidance", persist_directory: str | Path | None = None) -> None:
        self.embedding_service = EmbeddingService()
        self.embedding_model = self.embedding_service.model_name if self.embedding_service.client is not None else "chromadb-default"
        path = Path(persist_directory) if persist_directory is not None else settings.chroma_path
        if chromadb is None:
            self.client = _InMemoryClient(path)
            self.collection = self.client.get_or_create_collection(name=collection_name)
            return
        self.client = chromadb.PersistentClient(path=str(path))
        metadata = {"embedding_model": self.embedding_model}
        self.collection = self.client.get_or_create_collection(name=collection_name, metadata=metadata)
        stored_model = (self.collection.metadata or {}).get("embedding_model")
        if stored_model != self.embedding_model:
            self.client.delete_collection(name=collection_name)
            self.collection = self.client.create_collection(name=collection_name, metadata=metadata)

    def add_documents(self, documents: list[dict[str, str]], embeddings: list[list[float]] | None = None) -> None:
        if not documents:
            return
        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict[str, str]] = []
        for doc in documents:
            ids.append(doc["id"])
            texts.append(doc["text"])
            metadatas.append({
                "document_name": doc.get("document_name", doc["id"]),
                "section": doc.get("id", "general"),
                "chunk_id": doc["id"],
                "document_version": doc.get("document_version", "v1"),
                "source_type": doc.get("source_type", "synthetic_guidance"),
            })

        if embeddings is None and self.embedding_service.client is not None:
            embeddings = [self.embedding_service.embed(text) for text in texts]
        payload: dict[str, Any] = {"ids": ids, "documents": texts, "metadatas": metadatas}
        if embeddings is not None:
            payload["embeddings"] = embeddings
        self.collection.upsert(**payload)

    def ingest_documents(self, documents: list[dict[str, str]]) -> None:
        self.add_documents(documents)

    def query(self, query_text: str, limit: int = 3) -> list[str]:
        if self.embedding_service.client is not None:
            results = self.collection.query(
                query_embeddings=[self.embedding_service.embed(query_text)],
                n_results=limit,
            )
        else:
            results = self.collection.query(query_texts=[query_text], n_results=limit)
        docs = results.get("documents", [[]])[0]
        return [str(doc) for doc in docs]

    def count(self) -> int:
        return self.collection.count()
