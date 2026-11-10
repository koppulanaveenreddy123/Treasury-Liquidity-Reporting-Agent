from __future__ import annotations

from app.services.anomaly_service import AnomalyService


def test_anomaly_service_flags_negatives() -> None:
    anomalies = AnomalyService().detect_anomalies({"net_cash_available": -10.0, "lcr_ratio": 1.2})
    assert any(item.metric_name == "net_cash_available" for item in anomalies)


def test_anomaly_service_flags_high_lcr() -> None:
    anomalies = AnomalyService().detect_anomalies({"net_cash_available": 100.0, "lcr_ratio": 3.0})
    assert any(item.metric_name == "lcr_ratio" for item in anomalies)
