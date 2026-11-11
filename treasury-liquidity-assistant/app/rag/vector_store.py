from __future__ import annotations

from typing import Any

try:
    import chromadb
except ModuleNotFoundError:  # pragma: no cover - fallback for lightweight environments
    chromadb = None


class _InMemoryCollection:
    def __init__(self) -> None:
        self._documents: list[str] = []

    def add(self, *, ids: list[str], documents: list[str], metadatas: list[dict[str, str]]) -> None:
        for doc_id, document, metadata in zip(ids, documents, metadatas, strict=False):
            self._documents.append({"id": doc_id, "document": document, "metadata": metadata})

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


class _InMemoryClient:
    def __init__(self) -> None:
        self._collections: dict[str, _InMemoryCollection] = {}

    def get_or_create_collection(self, *, name: str) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection()
        return self._collections[name]


class VectorStore:
    """Public Chroma vector store for synthetic Treasury guidance only."""

    def __init__(self, collection_name: str = "treasury_guidance") -> None:
        if chromadb is None:
            self.client = _InMemoryClient()
            self.collection = self.client.get_or_create_collection(name=collection_name)
            return
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

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

        payload: dict[str, Any] = {"ids": ids, "documents": texts, "metadatas": metadatas}
        if embeddings is not None:
            payload["embeddings"] = embeddings
        self.collection.add(**payload)

    def ingest_documents(self, documents: list[dict[str, str]]) -> None:
        self.add_documents(documents)

    def query(self, query_text: str, limit: int = 3) -> list[str]:
        results = self.collection.query(query_texts=[query_text], n_results=limit)
        docs = results.get("documents", [[]])[0]
        return [str(doc) for doc in docs]
