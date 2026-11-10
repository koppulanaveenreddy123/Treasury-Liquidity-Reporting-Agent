from __future__ import annotations

import json
import time
from pathlib import Path

from pydantic import ValidationError

from app.config import settings
from app.models.treasury import CollateralRecord
from app.services.freshness_service import FreshnessService


class CollateralTool:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else settings.data_dir
        self.freshness_service = FreshnessService()

    def load_collateral(self, scenario: str = "healthy") -> list[CollateralRecord]:
        with (self.data_dir / "collateral.json").open("r", encoding="utf-8") as handle:
            rows = json.load(handle)
        filtered = [row for row in rows if row.get("scenario") == scenario]
        return [CollateralRecord.model_validate(row) for row in filtered]

    def get_collateral_data(self, business_date: str) -> dict:
        start = time.perf_counter()
        try:
            with (self.data_dir / "collateral.json").open("r", encoding="utf-8") as handle:
                rows = json.load(handle)
            records = [CollateralRecord.model_validate(row) for row in rows if row.get("business_date") == business_date]
            if not records:
                return {"success": False, "record_count": 0, "records": [], "execution_time_ms": round((time.perf_counter() - start) * 1000, 2), "error_message": "No records for business date", "source_system": "CollateralHub", "freshness_status": "CRITICAL", "is_stale": True, "data_age_seconds": 0}
            latest_timestamp = max(item.extraction_timestamp for item in records)
            age_seconds = self.freshness_service.get_age_seconds(latest_timestamp, reference_date=business_date)
            freshness = self.freshness_service.get_freshness_status(age_seconds)
            return {"tool_name": "get_collateral_data", "source_system": "CollateralHub", "business_date": business_date, "latest_extraction_timestamp": latest_timestamp, "data_age_seconds": age_seconds, "freshness_status": freshness, "is_stale": age_seconds > 1800, "record_count": len(records), "records": [item.model_dump(mode="json") for item in records], "execution_time_ms": round((time.perf_counter() - start) * 1000, 2), "success": True, "error_message": None}
        except (FileNotFoundError, json.JSONDecodeError, ValidationError) as exc:
            return {"tool_name": "get_collateral_data", "source_system": "CollateralHub", "business_date": business_date, "latest_extraction_timestamp": None, "data_age_seconds": 0, "freshness_status": "CRITICAL", "is_stale": True, "record_count": 0, "records": [], "execution_time_ms": round((time.perf_counter() - start) * 1000, 2), "success": False, "error_message": str(exc)}
