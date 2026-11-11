from __future__ import annotations

import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("STREAMLIT_API_TIMEOUT_SECONDS", "60"))

st.set_page_config(page_title="Treasury Liquidity Reporting Assistant", layout="wide")

st.title("Treasury & Liquidity Reporting Assistant")
st.caption("Educational MVP. Human review is mandatory before any report is released.")

scenario = st.selectbox("Scenario", ["healthy", "stale", "outlier"])
run_id = st.text_input("Run ID", value="demo-run-001")

if st.button("Generate draft report"):
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/reports/generate",
            json={"run_id": run_id, "scenario": scenario, "human_approved": False},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.ok:
            payload = response.json()
            st.json(payload)
        else:
            st.error(f"API error ({response.status_code}): {response.text}")
    except requests.exceptions.Timeout:
        st.error(
            f"The API did not respond within {REQUEST_TIMEOUT_SECONDS} seconds. "
            "Check that the FastAPI service is running and that the report generation pipeline is not blocked."
        )
    except requests.exceptions.RequestException as exc:
        st.error(f"Request failed: {exc}")

st.subheader("Service status")
for endpoint in ["/health", "/ready"]:
    try:
        result = requests.get(f"{API_BASE}{endpoint}", timeout=REQUEST_TIMEOUT_SECONDS)
        st.write(f"{endpoint}: {result.status_code} {result.text}")
    except requests.exceptions.Timeout:
        st.warning(
            f"{endpoint} timed out after {REQUEST_TIMEOUT_SECONDS}s. "
            "The backend may still be starting or processing a report."
        )
    except Exception as exc:  # pragma: no cover
        st.warning(f"{endpoint} unavailable: {exc}")
