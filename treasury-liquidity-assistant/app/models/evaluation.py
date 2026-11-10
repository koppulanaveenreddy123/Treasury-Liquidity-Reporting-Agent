from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Ground truth evaluation result for a scenario."""

    scenario: str
    pass_status: bool
    expected_metrics: dict[str, float] = Field(default_factory=dict)
    actual_metrics: dict[str, float] = Field(default_factory=dict)
    delta: dict[str, float] = Field(default_factory=dict)
