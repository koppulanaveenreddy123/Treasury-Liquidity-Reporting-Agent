from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class AlertService:
    """Build structured alert payloads for current treasury conditions."""

    def __init__(self) -> None:
        self._active_alerts: list[dict[str, Any]] = []

    def set_alerts(self, alerts: list[dict[str, Any]]) -> None:
        self._active_alerts = alerts

    def get_active_alerts(self) -> list[dict[str, Any]]:
        return self._active_alerts

    def evaluate_alerts(
        self,
        *,
        report_status: str | None = None,
        source_freshness: Mapping[str, Any] | None = None,
        evaluation_passed: bool | None = None,
        metrics: Mapping[str, Any] | None = None,
        human_review_status: str | None = None,
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []

        stale_sources = []
        if source_freshness:
            stale_sources = [
                {"source_system": source_name, "source_age_seconds": source_meta.get("source_age_seconds", 0)}
                for source_name, source_meta in source_freshness.items()
                if source_meta.get("is_stale")
            ]

        if stale_sources:
            alerts.append(
                {
                    "name": "TreasurySourceStale",
                    "severity": "warning",
                    "status": "active",
                    "summary": "Treasury source data is stale",
                    "description": "One or more source systems have not refreshed within the acceptable freshness window.",
                    "trigger": "source_freshness",
                    "details": stale_sources,
                }
            )

        if report_status == "BLOCKED":
            alerts.append(
                {
                    "name": "BlockedReport",
                    "severity": "critical",
                    "status": "active",
                    "summary": "Blocked report requires remediation",
                    "description": "The report is blocked due to stale data or failed validation and cannot be approved.",
                    "trigger": "report_status",
                    "details": {"report_status": report_status},
                }
            )

        if human_review_status in {"PENDING", "PENDING_REVIEW"}:
            alerts.append(
                {
                    "name": "PendingHumanReview",
                    "severity": "warning",
                    "status": "active",
                    "summary": "Draft report awaiting review",
                    "description": "At least one treasury report is pending formal human approval before release.",
                    "trigger": "human_review_status",
                    "details": {"human_review_status": human_review_status},
                }
            )

        if evaluation_passed is False:
            alerts.append(
                {
                    "name": "LiquidityEvaluationBelowThreshold",
                    "severity": "critical",
                    "status": "active",
                    "summary": "Automated evaluation failed threshold check",
                    "description": "The generated liquidity report appears anomalous and requires escalation for review.",
                    "trigger": "evaluation_result",
                    "details": {
                        "passed": False,
                    },
                }
            )

        liquidity_ratio = None
        if metrics is not None:
            try:
                liquidity_ratio = float(metrics.get("simplified_liquidity_coverage_ratio", 0.0))
            except (TypeError, ValueError):
                liquidity_ratio = None

        if liquidity_ratio is not None and liquidity_ratio < 1.0:
            alerts.append(
                {
                    "name": "LiquidityRatioAtRisk",
                    "severity": "critical",
                    "status": "active",
                    "summary": "Liquidity ratio below required level",
                    "description": "The latest liquidity ratio is below the safe operating threshold and should be treated as a reporting risk.",
                    "trigger": "liquidity_ratio",
                    "details": {"simplified_liquidity_coverage_ratio": liquidity_ratio},
                }
            )

        return alerts


alert_service = AlertService()
