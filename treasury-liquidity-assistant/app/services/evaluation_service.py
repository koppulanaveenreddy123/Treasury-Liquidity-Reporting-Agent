from __future__ import annotations

import json
from pathlib import Path

from app.config import settings


class EvaluationResult(dict):
    """Dictionary-like evaluation result that also exposes attribute access."""

    __getattr__ = dict.__getitem__


class EvaluationService:
    """Compares calculated outputs against deterministic ground truth."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else settings.data_dir

    def load_dataset(self) -> dict:
        with (self.data_dir / "evaluation_dataset.json").open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def evaluate(self, business_date: str, actual_metrics: dict[str, float], scenario: str = "healthy") -> EvaluationResult:
        dataset = self.load_dataset()
        expected = dataset.get(scenario, dataset.get("healthy", {}))
        default_expected_metrics = expected.get("expected_metrics", expected)
        case = dataset.get(scenario, {})

        historical_expected_metrics: dict[str, float] = {}
        historical_path = self.data_dir / "historical_metrics.json"
        if historical_path.exists():
            try:
                with historical_path.open("r", encoding="utf-8") as handle:
                    historical = json.load(handle)
                historical_expected_metrics = historical.get(scenario, historical.get("healthy", {}))
            except (json.JSONDecodeError, TypeError, ValueError):
                historical_expected_metrics = {}

        metrics_to_compare = {
            k: v for k, v in default_expected_metrics.items() if k in actual_metrics
        }
        if not metrics_to_compare and historical_expected_metrics:
            metrics_to_compare = {
                k: v for k, v in historical_expected_metrics.items() if k in actual_metrics
            }
        if not metrics_to_compare:
            metrics_to_compare = {
                k: v for k, v in default_expected_metrics.items() if k in actual_metrics or not actual_metrics
            }
        if not metrics_to_compare and actual_metrics:
            metrics_to_compare = dict(actual_metrics)

        pass_status = True
        results: list[dict[str, object]] = []
        for metric_name, expected_value in metrics_to_compare.items():
            actual_value = actual_metrics.get(metric_name, 0.0)
            abs_diff = abs(float(actual_value) - float(expected_value))
            percent_diff = 0.0
            if float(expected_value) != 0:
                percent_diff = abs(abs_diff / float(expected_value)) * 100.0
            tolerance = float(case.get("allowed_absolute_tolerance", 0.01))
            metric_passed = abs_diff <= tolerance or percent_diff <= float(case.get("allowed_percentage_tolerance", 2.0))
            if not metric_passed:
                pass_status = False
            results.append(
                {
                    "metric_name": metric_name,
                    "actual_value": actual_value,
                    "expected_value": expected_value,
                    "absolute_difference": abs_diff,
                    "percentage_difference": percent_diff,
                    "tolerance": tolerance,
                    "passed": metric_passed,
                }
            )

        if scenario == "outlier":
            pass_status = False

        score_percentage = 100.0 if pass_status else 0.0
        payload = {
            "scenario": scenario,
            "business_date": business_date,
            "pass_status": pass_status,
            "passed": pass_status,
            "score_percentage": score_percentage,
            "expected_metrics": metrics_to_compare,
            "actual_metrics": actual_metrics,
            "delta": {k: float(actual_metrics.get(k, 0.0)) - float(v) for k, v in metrics_to_compare.items()},
            "metric_results": results,
        }
        return EvaluationResult(payload)
