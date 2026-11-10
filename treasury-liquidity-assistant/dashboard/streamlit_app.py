from __future__ import annotations

import json

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Treasury Liquidity Reporting Assistant", layout="wide")

st.title("Treasury & Liquidity Reporting Assistant")
st.caption("Educational MVP. Human review is mandatory before any report is released.")

scenario = st.selectbox("Scenario", ["healthy", "stale", "outlier"])
run_id = st.text_input("Run ID", value="demo-run-001")

if st.button("Generate draft report"):
    response = requests.post(
        f"{API_BASE}/api/v1/reports/generate",
        json={"run_id": run_id, "scenario": scenario, "human_approved": False},
        timeout=10,
    )
    if response.ok:
        payload = response.json()
        st.json(payload)
    else:
        st.error(response.text)

st.subheader("Service status")
for endpoint in ["/health", "/ready"]:
    try:
        result = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        st.write(f"{endpoint}: {result.status_code} {result.text}")
    except Exception as exc:  # pragma: no cover
        st.warning(f"{endpoint} unavailable: {exc}")
