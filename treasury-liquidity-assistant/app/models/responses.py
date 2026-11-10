from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    """Response model for generated report drafts."""

    report_id: str = Field(..., description="Identifier for the generated report draft")
    scenario: str = Field(..., description="Scenario used to produce the report")
    status: str = Field(..., description="Current lifecycle status for the report")
    requires_human_approval: bool = Field(..., description="Whether a human review is mandatory")
    summary: str = Field(..., description="Short summary of report output")
    recommendations: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response model for health endpoints."""

    status: str
    service: str
