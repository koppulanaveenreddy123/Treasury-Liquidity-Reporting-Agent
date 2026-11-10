from __future__ import annotations

from app.models.anomaly import AnomalyRecord


class AnomalyService:
    """Flag suspicious numerical behavior in liquidity metrics."""

    def detect_anomalies(self, metrics: dict[str, float]) -> list[AnomalyRecord]:
        anomalies: list[AnomalyRecord] = []
        for name, value in metrics.items():
            if value < 0:
                anomalies.append(
                    AnomalyRecord(
                        metric_name=name,
                        severity="high",
                        description="Metric is negative and may indicate data issues or an outlier scenario.",
                        record_ids=[],
                    )
                )
            if name == "lcr_ratio" and value > 2.5:
                anomalies.append(
                    AnomalyRecord(
                        metric_name=name,
                        severity="medium",
                        description="LCR ratio exceeds the typical educational threshold and may be suspicious.",
                        record_ids=[],
                    )
                )
        return anomalies

    def detect_anomalies_for_report(
        self, metrics: dict[str, float], freshness: dict[str, dict], business_date: str
    ) -> list[dict[str, object]]:
        return [
            {
                "detected": True,
                "anomaly_type": "STALE_SOURCE",
                "metric_name": "source_freshness",
                "source_system": next(iter(freshness), "Unknown"),
                "current_value": 0,
                "expected_range": "0-1800 seconds",
                "severity": "CRITICAL",
                "reason": "Source is stale and should be reviewed before approval.",
                "detected_at": "now",
            }
        ] if any(meta.get("is_stale") for meta in freshness.values()) else []
