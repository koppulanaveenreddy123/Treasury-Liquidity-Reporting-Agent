from __future__ import annotations


class Chunker:
    """Split text into small, retrievable chunks."""

    def chunk(self, text: str, chunk_size: int = 500) -> list[str]:
        """Break a document into manageable chunks."""
        words = text.split()
        chunks: list[str] = []
        for index in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[index : index + chunk_size]))
        return chunks or [text]
