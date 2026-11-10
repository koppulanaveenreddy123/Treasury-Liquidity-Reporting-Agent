from __future__ import annotations

from pydantic import BaseModel, Field


class LineageTrace(BaseModel):
    """Trace object linking a metric to underlying source records."""

    metric_name: str
    source_record_ids: list[str] = Field(default_factory=list)
    calculation: str
    notes: str = ""