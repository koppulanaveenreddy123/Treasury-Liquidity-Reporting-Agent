from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.agent.orchestrator import Orchestrator
from app.models.requests import GenerateReportRequest
from app.models.review import ReviewDecisionRequest, ReviewRecord
from app.observability.metrics import HUMAN_REVIEWS, LAST_EVALUATION_SCORE, LAST_LIQUIDITY_RATIO, PENDING_REVIEW_REPORTS, REPORT_REQUESTS
from app.services.report_repository import ReportRepository

logger = logging.getLogger("treasury_app")
router = APIRouter(prefix="/api/v1", tags=["reports"])
repository = ReportRepository()


@router.post("/reports/generate")
async def generate_report(payload: GenerateReportRequest) -> dict:
    orchestrator = Orchestrator()
    report = orchestrator.generate_report(
        business_date="2026-11-06",
        scenario=payload.scenario,
        question="Treasury liquidity review",
        human_review_status="PENDING",
    )
    repository.save_report(report)
    REPORT_REQUESTS.labels(status="success").inc()
    PENDING_REVIEW_REPORTS.set(len(repository.list_reports()))
    LAST_LIQUIDITY_RATIO.set(float(report["calculated_metrics"].get("simplified_liquidity_coverage_ratio", 0)))
    LAST_EVALUATION_SCORE.set(float(report["evaluation_result"].get("score_percentage", 0)))
    response = {
        "status": "draft" if report.get("report_status") == "DRAFT" else report.get("report_status", "draft").lower(),
        "requires_human_approval": True,
        "report_id": report["report_id"],
        "scenario": payload.scenario,
        "summary": report.get("narrative", ""),
        "recommendations": [],
        "metrics": {k: float(v) for k, v in report.get("calculated_metrics", {}).items()},
        "warnings": [],
    }
    return response


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> dict:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/lineage")
async def get_lineage(report_id: str) -> dict:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "lineage": report.get("lineage", {})}


@router.get("/reports/{report_id}/lineage/{metric_name}")
async def get_metric_lineage(report_id: str, metric_name: str) -> dict:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    metric_lineage = report.get("lineage", {}).get(metric_name)
    if metric_lineage is None:
        raise HTTPException(status_code=404, detail="Metric lineage not found")
    return {"report_id": report_id, "metric_name": metric_name, "lineage": metric_lineage}


@router.post("/reports/{report_id}/review")
async def review_report(report_id: str, payload: ReviewDecisionRequest) -> dict:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.get("report_status") == "BLOCKED":
        if payload.decision == "REJECTED":
            report["report_status"] = "REJECTED"
            report["human_review_status"] = "REJECTED"
        else:
            raise HTTPException(status_code=409, detail="Report cannot be approved while blocking conditions exist.")

    if payload.decision == "APPROVED":
        if report.get("report_status") == "BLOCKED":
            raise HTTPException(status_code=409, detail="Report cannot be approved while blocking conditions exist.")
        report["report_status"] = "APPROVED"
        report["human_review_status"] = "APPROVED"
    elif payload.decision == "REJECTED":
        report["report_status"] = "REJECTED"
        report["human_review_status"] = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or REJECTED")

    review_id = f"review-{uuid.uuid4().hex[:8]}"
    review = {
        "review_id": review_id,
        "report_id": report_id,
        "decision": payload.decision,
        "reviewer": payload.reviewer,
        "comment": payload.comment,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "trace_id": report.get("trace_id", ""),
    }
    repository.save_review(review)
    HUMAN_REVIEWS.labels(decision=payload.decision).inc()
    return {"status": "ok", "review": review, "report": report}
