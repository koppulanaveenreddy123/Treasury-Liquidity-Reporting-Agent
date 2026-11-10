# Treasury & Liquidity Reporting Assistant

A training-focused MVP for treasury analysts to assemble end-of-day liquidity reporting using synthetic data sources, deterministic calculations, retrieval-augmented guidance, and a human approval gate.

This project is intentionally educational and not a production banking system.

## Goals

- Retrieve synthetic positions, expected cash flows, and collateral data from three mock sources.
- Compute simplified liquidity metrics deterministically.
- Validate metrics against ground truth and identify anomalies.
- Use ChromaDB and retrieval to ground guidance from treasury policy documents.
- Generate a draft narrative with an LLM, or a deterministic mock fallback.
- Preserve lineage from source record IDs to each metric.
- Require explicit human approval before any report can be released.

## Stack

- Python 3.11
- FastAPI
- Pydantic
- Streamlit
- ChromaDB
- sentence-transformers
- OpenAI-compatible LLM interface
- OpenTelemetry + Jaeger
- Prometheus + Grafana
- Pytest
- Docker Compose

## Local run

This project is validated on Python 3.11.x. Do not use Python 3.14 with the current dependency stack because the transitive `tokenizers`/PyO3 build fails on 3.14.

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -V
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If you are on macOS/Linux, use:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

## Docker Compose

```bash
docker compose up --build
```

## Notes

- The application never auto-submits a report.
- All outputs should be reviewed by a human before release.
- This repository intentionally uses synthetic data only.
