from __future__ import annotations

import json

from app.services.calculation_service import CalculationService


def test_net_cash_available_calculation() -> None:
    with open("app/data/positions.json", "r", encoding="utf-8") as handle:
        positions = [item for item in json.load(handle) if item["scenario"] == "healthy"]
    with open("app/data/cashflows.json", "r", encoding="utf-8") as handle:
        cashflows = [item for item in json.load(handle) if item["scenario"] == "healthy"]
    with open("app/data/collateral.json", "r", encoding="utf-8") as handle:
        collateral = [item for item in json.load(handle) if item["scenario"] == "healthy"]

    result = CalculationService().calculate_net_cash_available(positions, cashflows, collateral)
    assert result.metric_name == "net_cash_available"
    assert result.value == 2450000.0


def test_lcr_ratio_calculation() -> None:
    with open("app/data/positions.json", "r", encoding="utf-8") as handle:
        positions = [item for item in json.load(handle) if item["scenario"] == "healthy"]
    with open("app/data/cashflows.json", "r", encoding="utf-8") as handle:
        cashflows = [item for item in json.load(handle) if item["scenario"] == "healthy"]
    with open("app/data/collateral.json", "r", encoding="utf-8") as handle:
        collateral = [item for item in json.load(handle) if item["scenario"] == "healthy"]

    result = CalculationService().calculate_lcr_ratio(positions, cashflows, collateral)
    assert result.metric_name == "lcr_ratio"
    assert round(result.value, 2) == 1.5
