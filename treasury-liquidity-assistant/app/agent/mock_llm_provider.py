from __future__ import annotations

import json

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
        guidance_section = prompt.partition("RETRIEVED TREASURY GUIDANCE\n")[2].partition("\n\nNUMERICAL EVALUATION")[0].strip()
        guidance_text = guidance_section.removeprefix("- ").replace("\n- ", " ").replace("\n", " ").strip()
        guidance_text = " ".join(guidance_text.split())
        if guidance_text == "No Treasury guidance retrieved.":
            guidance_text = ""

        recommendations: list[str] = []
        guidance_lower = guidance_text.lower()
        if "fresh" in guidance_lower or "timestamp" in guidance_lower:
            recommendations.append("Verify source extraction timestamps and refresh stale feeds before release, following the retrieved freshness guidance.")
        if "human review" in guidance_lower or "reviewer" in guidance_lower:
            recommendations.append("Keep the report in draft until a human reviewer confirms the source lineage and review checks described in the retrieved guidance.")
        if not recommendations and guidance_text:
            recommendations.append("Review the retrieved Treasury guidance and apply its controls before releasing this draft.")
        if not recommendations:
            recommendations.append("Do not release this report until its source data and required human review have been verified.")

        summary = (
            f"Draft treasury liquidity report. Retrieved guidance: {guidance_text[:900]}"
            if guidance_text
            else "Draft treasury liquidity report. No Treasury guidance was retrieved; human review is required."
        )
        return json.dumps({"summary": summary, "recommendations": recommendations})
