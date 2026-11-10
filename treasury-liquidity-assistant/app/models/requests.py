from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    """Request body for reporting workflows in the educational demo."""

    run_id: str = Field(..., description="Unique run identifier for the report generation request")
    scenario: Literal["healthy", "stale", "outlier"] = Field(
        "healthy",
        description="Scenario name to generate metrics for.",
    )
    human_approved: bool = Field(False, description="Explicit approval received from a human reviewer.")
