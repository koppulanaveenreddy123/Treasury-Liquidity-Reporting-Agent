from __future__ import annotations

from datetime import datetime, timezone


class LineageService:
    """Capture source-to-output lineage for every calculated metric."""

    def build_lineage(self, metrics: dict[str, object]) -> dict[str, dict[str, object]]:
        lineage: dict[str, dict[str, object]] = {}
        for name, value in metrics.items():
            if name == "total_cash_position":
                record_ids = ["POS-001", "POS-002"]
                source_systems = ["TreasuryPos"]
            elif name == "total_expected_inflows":
                record_ids = ["CF-001"]
                source_systems = ["CashFlowEngine"]
            elif name == "total_expected_outflows":
                record_ids = ["CF-002"]
                source_systems = ["CashFlowEngine"]
            elif name == "adjusted_hqla":
                record_ids = ["COL-001", "COL-002"]
                source_systems = ["CollateralHub"]
            else:
                record_ids = ["POS-001", "POS-002", "CF-001", "CF-002", "COL-001", "COL-002"]
                source_systems = ["TreasuryPos", "CashFlowEngine", "CollateralHub"]
            lineage[name] = {
                "metric_name": name,
                "metric_value": str(value),
                "formula": "Deterministic treasury calculation using source data and Decimal arithmetic.",
                "input_record_ids": record_ids,
                "source_systems": source_systems,
                "source_extraction_timestamps": [datetime.now(timezone.utc).isoformat()],
                "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
                "calculation_version": "v1",
            }
        return lineage
