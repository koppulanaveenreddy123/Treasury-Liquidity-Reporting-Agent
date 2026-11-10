from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ReviewDecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"] = Field(..., description="Human review decision for the report.")
    reviewer: str = Field(default="unknown", description="Name or ID of the reviewer.")
    comment: str = Field(default="", description="Reason for approval or rejection.")


class ReviewRecord(BaseModel):
    review_id: str
    report_id: str
    decision: str
    reviewer: str
    comment: str
    reviewed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trace_id: str = ""
