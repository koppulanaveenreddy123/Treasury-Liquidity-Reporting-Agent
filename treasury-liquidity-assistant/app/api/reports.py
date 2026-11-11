from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.agent.orchestrator import Orchestrator
from app.models.requests import GenerateReportRequest
from app.models.review import ReviewDecisionRequest, ReviewRecord
from app.observability.metrics import ACTIVE_ALERTS, HUMAN_REVIEWS, LAST_EVALUATION_SCORE, LAST_LIQUIDITY_RATIO, PENDING_REVIEW_REPORTS, REPORT_REQUESTS
from app.services.alert_service import alert_service
from app.services.report_repository import ReportRepository

logger = logging.getLogger("treasury_app")
router = APIRouter(prefix="/api/v1", tags=["reports"])
repository = ReportRepository()


def _build_warnings(report: dict) -> list[str]:
    warnings: list[str] = []
    for anomaly in report.get("anomalies", []):
        if anomaly.get("detected"):
            warnings.append(f"{anomaly.get('anomaly_type', 'ANOMALY')}: {anomaly.get('reason', 'Manual review required.')}")

    for source_name, source_meta in report.get("source_freshness", {}).items():
        if source_meta.get("is_stale"):
            warnings.append(f"Source {source_name} is stale; data age is {source_meta.get('source_age_seconds')} seconds.")

    evaluation = report.get("evaluation_result", {})
    if evaluation.get("passed") is False:
        warnings.append("Automated evaluation failed the rule check and the report should not be released without review.")

    if report.get("report_status") == "BLOCKED":
        warnings.append("Report generation is blocked pending human review and remediation of data quality concerns.")

    return warnings


def _build_recommendations(report: dict) -> list[str]:
    recommendations: list[str] = []
    if report.get("report_status") == "BLOCKED":
        recommendations.append("Block release until stale source data is refreshed and the anomaly is reviewed by a human operator.")

    if any(meta.get("is_stale") for meta in report.get("source_freshness", {}).values()):
        recommendations.append("Refresh stale source feeds and rerun the report before approval.")

    for anomaly in report.get("anomalies", []):
        if anomaly.get("detected"):
            recommendations.append(f"Investigate the {anomaly.get('metric_name', 'affected metric')} anomaly before sign-off.")

    if not recommendations:
        recommendations.append("No immediate action required; continue with normal human review before final release.")

    return recommendations


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
    alerts = alert_service.evaluate_alerts(
        report_status=report.get("report_status"),
        source_freshness=report.get("source_freshness"),
        evaluation_passed=report.get("evaluation_result", {}).get("passed"),
        metrics=report.get("calculated_metrics"),
        human_review_status=report.get("human_review_status"),
    )
    alert_service.set_alerts(alerts)
    ACTIVE_ALERTS.set(len(alerts))
    response = {
        "status": "draft" if report.get("report_status") == "DRAFT" else report.get("report_status", "draft").lower(),
        "requires_human_approval": True,
        "report_id": report["report_id"],
        "scenario": payload.scenario,
        "summary": report.get("narrative", ""),
        "recommendations": _build_recommendations(report),
        "metrics": {k: float(v) for k, v in report.get("calculated_metrics", {}).items()},
        "warnings": _build_warnings(report),
        "alerts": alerts,
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
    alerts = alert_service.evaluate_alerts(
        report_status=report.get("report_status"),
        source_freshness=report.get("source_freshness"),
        evaluation_passed=report.get("evaluation_result", {}).get("passed"),
        metrics=report.get("calculated_metrics"),
        human_review_status=report.get("human_review_status"),
    )
    alert_service.set_alerts(alerts)
    ACTIVE_ALERTS.set(len(alerts))
    return {"status": "ok", "review": review, "report": report}


@router.get("/reports/{report_id}/alerts")
async def get_report_alerts(report_id: str) -> dict:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    alerts = alert_service.evaluate_alerts(
        report_status=report.get("report_status"),
        source_freshness=report.get("source_freshness"),
        evaluation_passed=report.get("evaluation_result", {}).get("passed"),
        metrics=report.get("calculated_metrics"),
        human_review_status=report.get("human_review_status"),
    )
    return {"report_id": report_id, "alerts": alerts, "count": len(alerts)}


@router.get("/alerts")
async def get_active_alerts() -> dict:
    alerts = alert_service.get_active_alerts()
    ACTIVE_ALERTS.set(len(alerts))
    return {"count": len(alerts), "alerts": alerts}
