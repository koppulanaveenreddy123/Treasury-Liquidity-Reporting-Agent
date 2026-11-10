from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

HEALTH_CHECKS = Counter("treasury_health_checks_total", "Number of health checks performed")
REPORT_REQUESTS = Counter("treasury_report_requests_total", "Number of report generation requests", labelnames=("status",))
TOOL_CALLS = Counter("treasury_tool_calls_total", "Number of data retrieval calls", labelnames=("tool", "status"))
LLM_CALLS = Counter("treasury_llm_calls_total", "Number of LLM calls", labelnames=("provider", "model", "status"))
RAG_RETRIEVALS = Counter("treasury_rag_retrieval_total", "Number of RAG retrievals", labelnames=("status",))
EVALUATIONS = Counter("treasury_evaluations_total", "Number of evaluations", labelnames=("result",))
ANOMALIES = Counter("treasury_anomalies_total", "Number of anomalies detected", labelnames=("type", "severity"))
STALE_SOURCES = Counter("treasury_stale_sources_total", "Number of stale source observations", labelnames=("source_system",))
HUMAN_REVIEWS = Counter("treasury_human_reviews_total", "Number of human review decisions", labelnames=("decision",))

REPORT_DURATION = Histogram("treasury_report_duration_seconds", "Report generation latency in seconds")
TOOL_DURATION = Histogram("treasury_tool_duration_seconds", "Tool execution latency in seconds", labelnames=("tool",))
LLM_DURATION = Histogram("treasury_llm_duration_seconds", "LLM latency in seconds", labelnames=("provider", "model"))
RAG_RETRIEVAL_DURATION = Histogram("treasury_rag_retrieval_duration_seconds", "RAG retrieval latency in seconds")
EVALUATION_DURATION = Histogram("treasury_evaluation_duration_seconds", "Evaluation latency in seconds")

SOURCE_AGE = Gauge("treasury_source_age_seconds", "Source age in seconds", labelnames=("source_system",))
LAST_LIQUIDITY_RATIO = Gauge("treasury_last_liquidity_ratio", "Latest simplified liquidity coverage ratio")
LAST_EVALUATION_SCORE = Gauge("treasury_last_evaluation_score", "Latest evaluation score")
PENDING_REVIEW_REPORTS = Gauge("treasury_pending_review_reports", "Count of reports pending review")
LAST_SUCCESS_TIMESTAMP = Gauge("treasury_last_success_timestamp_seconds", "Unix timestamp of the last successful report generation")
ACTIVE_ALERTS = Gauge("treasury_active_alerts", "Number of active alerts")


def setup_metrics() -> None:
    """Initialize application metric state."""
    ACTIVE_ALERTS.set(0)
    PENDING_REVIEW_REPORTS.set(0)
    LAST_LIQUIDITY_RATIO.set(0)
    LAST_EVALUATION_SCORE.set(0)


def metrics_payload() -> bytes:
    """Return Prometheus metrics bytes."""
    return generate_latest()
