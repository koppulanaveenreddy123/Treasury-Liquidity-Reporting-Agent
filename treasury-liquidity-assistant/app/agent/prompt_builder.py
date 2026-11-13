from __future__ import annotations

SYSTEM_INSTRUCTION = """You are a Treasury and Liquidity Reporting Assistant for an educational capstone.

All financial values provided to you have already been calculated deterministically.
Never perform new financial calculations.
Never modify, estimate, round, replace, or invent supplied financial values.
Use retrieved Treasury guidance only as explanatory context.
Highlight anomalies and stale sources.
Explicitly mention when human review is required.
Never approve a report.
Never describe the report as submitted to a regulator.
Never describe the simplified calculation as an official regulatory LCR.
Return valid JSON only, with a summary string and a recommendations array of strings.
Ground the summary and each recommendation in the retrieved Treasury guidance and supplied report facts.
Do not invent policies or make recommendations unsupported by the retrieved guidance.
"""


def build_prompt(
    metrics: dict[str, float],
    guidance: list[str],
    scenario: str,
    freshness: dict[str, object] | None = None,
    anomalies: list[dict[str, object]] | None = None,
    evaluation: dict[str, object] | None = None,
    review_status: str = "PENDING",
    question: str = "",
) -> str:
    guidance_text = "\n".join(f"- {item}" for item in guidance) if guidance else "- No Treasury guidance retrieved."
    metrics_text = "\n".join(f"{name}: {value}" for name, value in metrics.items())
    freshness_text = "\n".join(f"{name}: {value}" for name, value in (freshness or {}).items())
    anomaly_text = "\n".join(f"- {item.get('anomaly_type', 'UNKNOWN')}: {item.get('reason', '')}" for item in (anomalies or [])) or "- No anomalies detected."
    evaluation_text = str(evaluation or {"status": "PASS", "score": 100.0})
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        "USER QUESTION\n"
        f"{question or f'Prepare a short draft narrative for the {scenario} treasury liquidity report.'}\n\n"
        "DETERMINISTIC METRICS\n"
        f"{metrics_text}\n\n"
        "SOURCE FRESHNESS\n"
        f"{freshness_text}\n\n"
        "ANOMALIES\n"
        f"{anomaly_text}\n\n"
        "RETRIEVED TREASURY GUIDANCE\n"
        f"{guidance_text}\n\n"
        "NUMERICAL EVALUATION\n"
        f"{evaluation_text}\n\n"
        "HUMAN REVIEW STATUS\n"
        f"{review_status}\n\n"
        "MANDATORY RESPONSE FORMAT AND RULES\n"
        '{"summary":"Concise report narrative","recommendations":["Actionable recommendation grounded in retrieved guidance"]}\n'
        "- Return exactly one JSON object with the keys shown above.\n"
        "- Write a concise, fact-specific summary.\n"
        "- Include actionable recommendations that connect retrieved guidance to the report's freshness or anomalies.\n"
        "- Do not change any numbers.\n"
        "- Mention whether human review remains required.\n"
        "- Call out any stale source or anomaly.\n"
        "- Do not describe the report as submitted to a regulator.\n"
    )
