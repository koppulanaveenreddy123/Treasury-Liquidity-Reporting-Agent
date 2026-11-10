from __future__ import annotations

from app.exceptions import HumanApprovalRequired


class ReviewService:
    """Gate human approval before a report is released."""

    def validate_human_approval(self, human_approved: bool) -> None:
        """Require explicit approval before release is allowed."""
        if not human_approved:
            raise HumanApprovalRequired("A human reviewer must explicitly approve the report before any release.")

    def can_approve(
        self, report_status: str, evaluation_passed: bool, freshness_status: str | None = None
    ) -> bool:
        if report_status == "BLOCKED":
            return False
        if not evaluation_passed:
            return False
        if freshness_status == "CRITICAL":
            return False
        return True
