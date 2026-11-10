from __future__ import annotations

from app.rag.document_loader import DocumentLoader


def test_document_loader_reads_knowledge() -> None:
    docs = DocumentLoader(knowledge_dir="app/knowledge").load_documents()
    assert len(docs) >= 1
    assert docs[0]["text"].startswith("# ")
