from __future__ import annotations

from pydantic import BaseModel, Field


class AnomalyRecord(BaseModel):
    """Captured anomaly information in a report or evaluation."""

    metric_name: str
    severity: str
    description: str
    record_ids: list[str] = Field(default_factory=list)
