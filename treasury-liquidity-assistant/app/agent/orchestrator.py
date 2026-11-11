from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from opentelemetry import trace

from app.agent.llm_provider import LLMProvider, OpenAICompatibleLLMProvider
from app.agent.mock_llm_provider import MockLLMProvider
from app.agent.prompt_builder import build_prompt
from app.config import settings
from app.observability.metrics import (
    ANOMALIES,
    EVALUATIONS,
    HUMAN_REVIEWS,
    LAST_EVALUATION_SCORE,
    LAST_LIQUIDITY_RATIO,
    LLM_CALLS,
    LLM_DURATION,
    PENDING_REVIEW_REPORTS,
    REPORT_DURATION,
    REPORT_REQUESTS,
    RAG_RETRIEVALS,
    RAG_RETRIEVAL_DURATION,
    SOURCE_AGE,
    STALE_SOURCES,
    TOOL_CALLS,
    TOOL_DURATION,
)
from app.observability.tracing import tracer_span
from app.rag.vector_store import VectorStore
from app.services.anomaly_service import AnomalyService
from app.services.calculation_service import CalculationService
from app.services.evaluation_service import EvaluationService
from app.services.freshness_service import FreshnessService
from app.services.lineage_service import LineageService
from app.services.review_service import ReviewService
from app.tools.cashflows_tool import CashFlowsTool
from app.tools.collateral_tool import CollateralTool
from app.tools.positions_tool import PositionsTool


class Orchestrator:
    """Coordinates retrieval, calculation, and narrative generation."""

    def __init__(self, llm_provider: LLMProvider | None = None, use_mock_llm: bool | None = None) -> None:
        effective_use_mock = settings.use_mock_llm if use_mock_llm is None else use_mock_llm
        self.llm_provider = llm_provider or (MockLLMProvider() if effective_use_mock else OpenAICompatibleLLMProvider())
        self.positions_tool = PositionsTool()
        self.cashflows_tool = CashFlowsTool()
        self.collateral_tool = CollateralTool()
        self.freshness_service = FreshnessService()
        self.calculation_service = CalculationService()
        self.anomaly_service = AnomalyService()
        self.evaluation_service = EvaluationService()
        self.lineage_service = LineageService()
        self.review_service = ReviewService()
        self.vector_store = VectorStore()

    def _load_freshness_metadata(self, source_name: str, record_count: int, latest_ts: str | None, source_age_seconds: int, business_date: str | None = None, scenario: str | None = None) -> dict[str, Any]:
        if business_date and latest_ts and latest_ts[:10] == business_date and scenario != "stale":
            source_age_seconds = 0
        if scenario == "stale":
            source_age_seconds = max(source_age_seconds, 3 * 60 * 60)
        status = self.freshness_service.get_freshness_status(source_age_seconds)
        is_stale = source_age_seconds > 1800
        SOURCE_AGE.labels(source_system=source_name).set(source_age_seconds)
        if is_stale:
            STALE_SOURCES.labels(source_system=source_name).inc()
        return {
            "source_name": source_name,
            "record_count": record_count,
            "latest_extraction_timestamp": latest_ts,
            "source_age_seconds": source_age_seconds,
            "freshness_status": status,
            "is_stale": is_stale,
        }

    def _get_guidance(self, query: str) -> tuple[list[str], dict[str, Any]]:
        try:
            documents = self.vector_store.query(query_text=query, limit=5)
            RAG_RETRIEVALS.labels(status="success").inc()
            return documents, {"status": "success", "count": len(documents)}
        except Exception:
            RAG_RETRIEVALS.labels(status="error").inc()
            return [], {"status": "error", "count": 0}

    def generate_report(self, business_date: str, scenario: str = "healthy", question: str = "", human_review_status: str = "PENDING") -> dict[str, Any]:
        report_id = f"rep-{uuid.uuid4().hex[:8]}"
        start = datetime.now(timezone.utc)
        trace_id = trace.get_current_span().get_span_context().trace_id if trace.get_current_span().get_span_context().is_valid else "n/a"

        with tracer_span("treasury.report.generate") as span:
            span.set_attribute("report.id", report_id)
            span.set_attribute("business.date", business_date)
            REPORT_REQUESTS.labels(status="success").inc()

            with tracer_span("treasury.positions.retrieve") as positions_span:
                positions = self.positions_tool.get_position_data(business_date=business_date, scenario=scenario)
                positions_span.set_attribute("source.system", "TreasuryPos")
                positions_span.set_attribute("source.record_count", positions.get("record_count", 0))
                positions_span.set_attribute("source.age_seconds", positions.get("data_age_seconds", 0))
                TOOL_CALLS.labels(tool="positions", status="success" if positions.get("success") else "error").inc()
                TOOL_DURATION.labels(tool="positions").observe(float(positions.get("execution_time_ms", 0)) / 1000.0)

            with tracer_span("treasury.cashflows.retrieve") as cashflow_span:
                cashflows = self.cashflows_tool.get_cashflow_data(business_date=business_date, scenario=scenario)
                cashflow_span.set_attribute("source.system", "CashFlowEngine")
                cashflow_span.set_attribute("source.record_count", cashflows.get("record_count", 0))
                cashflow_span.set_attribute("source.age_seconds", cashflows.get("data_age_seconds", 0))
                TOOL_CALLS.labels(tool="cashflows", status="success" if cashflows.get("success") else "error").inc()
                TOOL_DURATION.labels(tool="cashflows").observe(float(cashflows.get("execution_time_ms", 0)) / 1000.0)

            with tracer_span("treasury.collateral.retrieve") as collateral_span:
                collateral = self.collateral_tool.get_collateral_data(business_date=business_date, scenario=scenario)
                collateral_span.set_attribute("source.system", "CollateralHub")
                collateral_span.set_attribute("source.record_count", collateral.get("record_count", 0))
                collateral_span.set_attribute("source.age_seconds", collateral.get("data_age_seconds", 0))
                TOOL_CALLS.labels(tool="collateral", status="success" if collateral.get("success") else "error").inc()
                TOOL_DURATION.labels(tool="collateral").observe(float(collateral.get("execution_time_ms", 0)) / 1000.0)

            freshness = {
                "positions": self._load_freshness_metadata("TreasuryPos", positions.get("record_count", 0), positions.get("latest_extraction_timestamp"), positions.get("data_age_seconds", 0), business_date, scenario),
                "cashflows": self._load_freshness_metadata("CashFlowEngine", cashflows.get("record_count", 0), cashflows.get("latest_extraction_timestamp"), cashflows.get("data_age_seconds", 0), business_date, scenario),
                "collateral": self._load_freshness_metadata("CollateralHub", collateral.get("record_count", 0), collateral.get("latest_extraction_timestamp"), collateral.get("data_age_seconds", 0), business_date, scenario),
            }

            with tracer_span("treasury.source_freshness.validate") as freshness_span:
                freshness_span.set_attribute("source.system", "TreasuryPos,CashFlowEngine,CollateralHub")
                statuses = [value["freshness_status"] for value in freshness.values()]
                freshness_span.set_attribute("source.freshness.status", ",".join(statuses))

            metrics = self.calculation_service.calculate_all(
                positions=positions.get("records", []),
                cashflows=cashflows.get("records", []),
                collateral=collateral.get("records", []),
            )
            with tracer_span("treasury.metrics.calculate") as calc_span:
                calc_span.set_attribute("calculation.version", "v1")
                for name, value in metrics.items():
                    calc_span.set_attribute(f"metric.name.{name}", str(value))

            anomalies = self.anomaly_service.detect_anomalies_for_report(metrics, freshness, business_date)
            with tracer_span("treasury.anomaly.detect") as anomaly_span:
                for anomaly in anomalies:
                    anomaly_span.set_attribute(f"anomaly.{anomaly['anomaly_type']}.severity", anomaly.get("severity", "UNKNOWN"))
                    anomaly_span.set_attribute(f"anomaly.{anomaly['anomaly_type']}.detected", True)
                anomaly_span.set_attribute("anomaly.detected", bool(anomalies))
                anomaly_span.set_attribute("anomaly.count", len(anomalies))

            guidance_chunks, rag_meta = self._get_guidance(question or "liquidity review guidance and source freshness procedure")
            with tracer_span("treasury.rag.retrieve") as rag_span:
                rag_span.set_attribute("rag.collection", "treasury_guidance")
                rag_span.set_attribute("rag.chunk_count", len(guidance_chunks))
                rag_span.set_attribute("rag.document_names", "liquidity_reporting_overview,simplified_lcr_guidance,source_freshness_procedure,anomaly_review_guidance,human_review_procedure")
                RAG_RETRIEVAL_DURATION.observe(0.05)

            evaluation_result = self.evaluation_service.evaluate(business_date, metrics, scenario)
            with tracer_span("treasury.evaluation.run") as eval_span:
                eval_span.set_attribute("evaluation.passed", evaluation_result["passed"])
                eval_span.set_attribute("evaluation.score", evaluation_result["score_percentage"])
                EVALUATIONS.labels(result="pass" if evaluation_result["passed"] else "fail").inc()
                LAST_EVALUATION_SCORE.set(float(evaluation_result["score_percentage"]))

            lineage = self.lineage_service.build_lineage(metrics)
            with tracer_span("treasury.lineage.capture") as lineage_span:
                lineage_span.set_attribute("lineage.metric_count", len(lineage))

            llm_prompt = build_prompt(
                metrics={name: float(value) for name, value in metrics.items()},
                guidance=guidance_chunks,
                scenario=scenario,
                freshness=freshness,
                anomalies=anomalies,
                evaluation=evaluation_result,
                review_status=human_review_status,
            )
            provider_name = "mock"
            if isinstance(self.llm_provider, MockLLMProvider):
                narrative = self.llm_provider.generate(llm_prompt)
            else:
                provider_name = "openai"
                narrative = self.llm_provider.generate(llm_prompt)
            with tracer_span("treasury.llm.call") as llm_span:
                llm_span.set_attribute("llm.provider", provider_name)
                llm_span.set_attribute("llm.model", getattr(self.llm_provider, "model", "mock-model"))
                llm_span.set_attribute("llm.output_tokens", len(narrative.split()))
                LLM_CALLS.labels(provider=provider_name, model=getattr(self.llm_provider, "model", "mock-model"), status="success").inc()
                LLM_DURATION.labels(provider=provider_name, model=getattr(self.llm_provider, "model", "mock-model")).observe(0.15)

            report_status = "DRAFT"
            if any(freshness[source]["freshness_status"] == "CRITICAL" for source in freshness):
                report_status = "BLOCKED"
            if evaluation_result["passed"] is False:
                report_status = "BLOCKED"
            if report_status == "DRAFT":
                PENDING_REVIEW_REPORTS.inc()
            HUMAN_REVIEWS.labels(decision="PENDING").inc()
            LAST_LIQUIDITY_RATIO.set(float(metrics.get("simplified_liquidity_coverage_ratio", 0)))
            REPORT_DURATION.observe((datetime.now(timezone.utc) - start).total_seconds())

            payload = {
                "report_id": report_id,
                "business_date": business_date,
                "report_status": report_status,
                "human_review_status": human_review_status,
                "calculated_metrics": {name: str(value) for name, value in metrics.items()},
                "narrative": narrative,
                "source_summary": [
                    {
                        "source_system": source_name,
                        "freshness_status": source_meta["freshness_status"],
                        "is_stale": source_meta["is_stale"],
                        "data_age_seconds": source_meta["source_age_seconds"],
                        "latest_extraction_timestamp": source_meta["latest_extraction_timestamp"],
                        "record_count": source_meta["record_count"],
                    }
                    for source_name, source_meta in freshness.items()
                ],
                "source_freshness": freshness,
                "anomalies": anomalies,
                "retrieved_guidance": guidance_chunks,
                "evaluation_result": evaluation_result,
                "lineage": lineage,
                "trace_id": trace_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return payload
