from __future__ import annotations

from openai import OpenAI

from app.config import settings


class EmbeddingService:
    """OpenAI embedding wrapper for ChromaDB ingestion and semantic retrieval."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)

    def embed(self, text: str) -> list[float]:
        """Create an embedding for a chunk of text using the configured OpenAI model."""
        if self.client is None:
            raise RuntimeError("OpenAI embeddings require an API key.")
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
        )
        return response.data[0].embedding
