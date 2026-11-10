from __future__ import annotations

from typing import Any


class ReportRepository:
    """Simple in-memory repository for report drafts in the MVP."""

    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}
        self._reviews: list[dict[str, Any]] = []

    def save_report(self, report: dict[str, Any]) -> dict[str, Any]:
        """Persist a generated report to the in-memory repository."""
        self._reports[report["report_id"]] = report
        return report

    def list_reports(self) -> list[dict[str, Any]]:
        """Return all persisted reports."""
        return list(self._reports.values())

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        """Return a report by ID or None when it does not exist."""
        return self._reports.get(report_id)

    def save_review(self, review: dict[str, Any]) -> dict[str, Any]:
        """Persist a human review record."""
        self._reviews.append(review)
        return review

    def list_reviews(self) -> list[dict[str, Any]]:
        """Return all human review records."""
        return list(self._reviews)

    def save(self, report_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Backward-compatible alias for report persistence."""
        return self.save_report(payload)

    def get(self, report_id: str) -> dict[str, Any] | None:
        """Backward-compatible alias for report retrieval."""
        return self.get_report(report_id)
