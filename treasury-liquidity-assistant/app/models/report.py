from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SourceSummary(BaseModel):
    source_system: str
    freshness_status: str
    is_stale: bool
    data_age_seconds: int
    latest_extraction_timestamp: str | None = None
    record_count: int = 0


class ReportModel(BaseModel):
    report_id: str
    business_date: str
    report_status: str = "DRAFT"
    human_review_status: str = "PENDING"
    calculated_metrics: dict[str, Any] = Field(default_factory=dict)
    narrative: str = ""
    source_summary: list[SourceSummary] = Field(default_factory=list)
    source_freshness: dict[str, Any] = Field(default_factory=dict)
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_guidance: list[str] = Field(default_factory=list)
    evaluation_result: dict[str, Any] = Field(default_factory=dict)
    lineage: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = ""
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
