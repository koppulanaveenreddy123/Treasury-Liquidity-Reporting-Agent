from __future__ import annotations

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Sentence-transformer embedding wrapper."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """Create an embedding for a chunk of text."""
        return self.model.encode(text).tolist()
