from __future__ import annotations

from app.tools.cashflows_tool import CashFlowsTool
from app.tools.collateral_tool import CollateralTool
from app.tools.positions_tool import PositionsTool


def test_positions_tool_loads_data() -> None:
    items = PositionsTool(data_dir="app/data").load_positions("healthy")
    assert len(items) >= 1
    assert items[0].record_id.startswith("POS-")


def test_cashflow_tool_loads_data() -> None:
    items = CashFlowsTool(data_dir="app/data").load_cashflows("healthy")
    assert len(items) >= 1
    assert items[0].record_id.startswith("CF-")


def test_collateral_tool_loads_data() -> None:
    items = CollateralTool(data_dir="app/data").load_collateral("healthy")
    assert len(items) >= 1
    assert items[0].record_id.startswith("COL-")
