from __future__ import annotations

from datetime import datetime, timezone


class FreshnessService:
    """Assess cross-source freshness for mandatory treasury inputs."""

    DEFAULT_THRESHOLDS = {
        "HEALTHY": 30 * 60,
        "WARNING": 60 * 60,
    }

    def get_freshness_status(self, age_seconds: int) -> str:
        if age_seconds <= 30 * 60:
            return "HEALTHY"
        if age_seconds <= 60 * 60:
            return "WARNING"
        return "CRITICAL"

    def get_age_seconds(self, extraction_timestamp: str | None, reference_date: str | None = None) -> int:
        if not extraction_timestamp:
            return 0
        try:
            parsed = datetime.fromisoformat(extraction_timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            if reference_date is not None:
                try:
                    reference = datetime.fromisoformat(reference_date)
                except ValueError:
                    reference = None
                if reference is not None and parsed.date() == reference.date():
                    return 0
            now = datetime.now(timezone.utc)
            return max(0, int((now - parsed).total_seconds()))
        except ValueError:
            return 0
