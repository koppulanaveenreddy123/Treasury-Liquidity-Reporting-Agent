from __future__ import annotations

from app.rag.ingestion import IngestionService


def main() -> None:
    """Ingest treasury knowledge into ChromaDB."""
    service = IngestionService(knowledge_dir="app/knowledge")
    service.ingest()
    print("Knowledge ingested into ChromaDB.")


if __name__ == "__main__":
    main()
