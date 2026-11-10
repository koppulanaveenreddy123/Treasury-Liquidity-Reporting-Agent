from __future__ import annotations

from app.agent.llm_provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic fallback LLM for demo and evaluation environments."""

    def __init__(self, *, inject_bad_value: bool = False) -> None:
        self.inject_bad_value = inject_bad_value

    def generate(self, prompt: str) -> str:
        if self.inject_bad_value:
            return (
                "Treasury narrative: total_cash_position is 999999999.99 GBP, which is not an authoritative calculation. "
                "The values provided to the model were already calculated deterministically and must be reviewed by a human."
            )
        return (
            "You are a Treasury and Liquidity Reporting Assistant for an educational capstone. "
            "All financial values have already been calculated deterministically. Do not perform new financial calculations. "
            "Use Treasury guidance only as explanatory context. Highlight anomalies and stale sources. "
            "Explicitly mention that human review is required. Never approve a report. "
            "This is a draft narrative only."
        )
