from __future__ import annotations

from app.agent.mock_llm_provider import MockLLMProvider
from app.agent.orchestrator import Orchestrator
from app.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import VectorStore


def test_document_loader_reads_knowledge() -> None:
    docs = DocumentLoader(knowledge_dir="app/knowledge").load_documents()
    assert len(docs) >= 1
    assert docs[0]["text"].startswith("# ")


def test_vector_store_persists_guidance_across_instances(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "chroma_path", tmp_path / "chroma")
    monkeypatch.setattr(settings, "openai_api_key", "")
    guidance = "Source freshness procedures require checking extraction timestamps before reporting liquidity."

    writer = VectorStore()
    writer.ingest_documents([{"id": "freshness-0", "text": guidance}])

    reader = VectorStore()
    orchestrator = Orchestrator(llm_provider=MockLLMProvider())
    orchestrator.vector_store = reader
    report = orchestrator.generate_report(
        business_date="2026-11-13",
        question="source freshness procedures",
    )

    assert report["retrieved_guidance"] == [guidance]
    assert guidance in report["narrative"]
    assert any("freshness guidance" in item.lower() for item in report["recommendations"])
    assert report["rag_metadata"]["embedding_model"] == "chromadb-default"
    assert report["llm_provider"] == "mock"
    assert report["llm_model"] == "mock-model"
