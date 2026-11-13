from __future__ import annotations

from abc import ABC, abstractmethod

from openai import OpenAI

from app.config import settings


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return generated text from the provider."""


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.llm_model
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)

    def generate(self, prompt: str) -> str:
        if self.client is None:
            raise RuntimeError("OpenAI-compatible LLM provider requires an API key.")
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        return response.output_text
