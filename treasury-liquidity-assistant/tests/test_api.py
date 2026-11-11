from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_endpoint() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_generate_report_placeholder() -> None:
    response = client.post(
        "/api/v1/reports/generate",
        json={"run_id": "demo-001", "scenario": "healthy", "human_approved": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["requires_human_approval"] is True


def test_review_accepts_reviewer_and_comment() -> None:
    report_response = client.post(
        "/api/v1/reports/generate",
        json={"run_id": "demo-review-001", "scenario": "healthy", "human_approved": False},
    )
    assert report_response.status_code == 200
    report_id = report_response.json()["report_id"]

    review_response = client.post(
        f"/api/v1/reports/{report_id}/review",
        json={"decision": "REJECTED", "reviewer": "analyst", "comment": "Liquidity metrics below threshold."},
    )
    assert review_response.status_code == 200
    review_payload = review_response.json()["review"]
    assert review_payload["reviewer"] == "analyst"
    assert review_payload["comment"] == "Liquidity metrics below threshold."


def test_stale_scenario_is_blocked_and_rejects_approval() -> None:
    report_response = client.post(
        "/api/v1/reports/generate",
        json={"run_id": "stale-block-demo", "scenario": "stale", "human_approved": False},
    )
    assert report_response.status_code == 200
    payload = report_response.json()
    assert payload["status"] == "blocked"
    assert payload["warnings"]
    assert any("stale" in warning.lower() for warning in payload["warnings"])

    report_id = payload["report_id"]
    review_response = client.post(
        f"/api/v1/reports/{report_id}/review",
        json={"decision": "APPROVED", "reviewer": "analyst", "comment": "Approve stale data"},
    )
    assert review_response.status_code == 409
    assert "cannot be approved" in review_response.json()["detail"].lower()
