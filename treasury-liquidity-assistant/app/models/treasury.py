from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class TreasurySourceRecord(BaseModel):
    source_system: str
    source_record_id: str
    business_date: str
    extraction_timestamp: str
    currency: str
    data_status: str = "VALID"

    @property
    def record_id(self) -> str:
        return self.source_record_id


class PositionRecord(TreasurySourceRecord):
    position_type: str
    account_reference: str
    balance: Decimal
    amount_in_base_currency: Decimal


class CashflowRecord(TreasurySourceRecord):
    flow_type: str
    counterparty_reference: str
    amount: Decimal
    amount_in_base_currency: Decimal
    maturity_bucket: str


class CollateralRecord(TreasurySourceRecord):
    asset_type: str
    market_value: Decimal
    haircut_percentage: Decimal
    adjusted_value: Decimal
    liquidity_category: str
    currency: str = "GBP"


class ToolResult(BaseModel):
    tool_name: str
    source_system: str
    business_date: str
    latest_extraction_timestamp: str | None = None
    data_age_seconds: int = 0
    freshness_status: str = "HEALTHY"
    is_stale: bool = False
    record_count: int = 0
    records: list[dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    success: bool = True
    error_message: str | None = None


class LiquidityMetric(BaseModel):
    metric_name: str
    value: Decimal
    source_record_ids: list[str] = Field(default_factory=list)
    provenance: str = "deterministic-calculation"