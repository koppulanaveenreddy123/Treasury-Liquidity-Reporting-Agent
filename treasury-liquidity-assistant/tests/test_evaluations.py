from __future__ import annotations

from app.services.evaluation_service import EvaluationService


def test_evaluation_service_matches_expected_metrics() -> None:
    service = EvaluationService(data_dir="app/data")
    result = service.evaluate("healthy", {"net_cash_available": 2450000.0, "lcr_ratio": 1.5})
    assert result.pass_status is True
