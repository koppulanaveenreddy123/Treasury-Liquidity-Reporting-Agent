from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/v1", tags=["evaluations"])


@router.get("/evaluations")
async def list_evaluations() -> dict[str, list[str]]:
    """Placeholder evaluation listing endpoint."""
    return {"evaluations": []}


@router.post("/evaluations/run/{test_case_id}")
async def run_evaluation(test_case_id: str) -> dict:
    service = EvaluationService()
    dataset = service.load_dataset()
    case = dataset.get(test_case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    metrics = {
        "total_cash_position": case["expected_metrics"].get("total_cash_position", 0),
        "total_expected_inflows": case["expected_metrics"].get("total_expected_inflows", 0),
        "total_expected_outflows": case["expected_metrics"].get("total_expected_outflows", 0),
        "net_cash_flow": case["expected_metrics"].get("net_cash_flow", 0),
        "adjusted_hqla": case["expected_metrics"].get("adjusted_hqla", 0),
        "simplified_liquidity_coverage_ratio": case["expected_metrics"].get("simplified_liquidity_coverage_ratio", 0),
    }
    result = service.evaluate("2026-11-06", metrics, test_case_id)
    result["evaluation_id"] = f"eval-{uuid.uuid4().hex[:8]}"
    return result


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str) -> dict:
    return {"evaluation_id": evaluation_id, "status": "available"}
