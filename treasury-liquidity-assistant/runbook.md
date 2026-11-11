# Treasury & Liquidity Reporting Assistant Runbook

This runbook is for running the end-to-end demo, testing all scenario flows, and presenting the treasury liquidity assistant in a live environment.

## 1. Project objective

The project demonstrates an operational risk-control workflow for treasury liquidity reporting:

- pull data from mock treasury sources
- compute liquidity metrics
- detect stale or anomalous values
- check source freshness before release
- require explicit human approval before a report is finalised
- trace the report back to source data
- monitor metrics in Prometheus and Grafana
- inspect request traces in Jaeger

The key demo scenarios are:

- Healthy scenario: reporting flow works normally
- Stale scenario: source data freshness issue
- Outlier scenario: anomalous metric issue

This is best described as data drift / operational drift, not model drift.

## 2. Prerequisites

You need:

- Python 3.11
- Windows PowerShell (or a similar shell)
- Docker Desktop running for the monitoring stack
- Git
- OpenAI API key (optional if using mock mode)

## 3. Environment setup

From the project root:

```powershell
cd C:\Users\l76-labuser230610\Treasure-Liquidity-Reporting\treasury-liquidity-assistant
..\treasure\Scripts\Activate.ps1
python -V
pip install --upgrade pip
pip install -r requirements.txt
```

If your venv is not active, this is the typical activation command:

```powershell
..\treasure\Scripts\Activate.ps1
```

## 4. Configure environment variables

Create a `.env` file in the project root. Example:

```dotenv
OPENAI_API_KEY="<your-openai-key>"
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
USE_MOCK_LLM=false

APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
JAEGER_ENDPOINT=http://localhost:4318
PROMETHEUS_PORT=9090
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

Notes:

- If `USE_MOCK_LLM=false`, the app uses the configured OpenAI model
- If you do not want to use the real model yet, set `USE_MOCK_LLM=true`
- The embedding model used for Chroma must match the same model family used for retrieval and indexing

## 5. Rebuild the knowledge vector store

Run this from the project root:

```powershell
python -m scripts.ingest_knowledge
```

Expected output:

```text
Knowledge ingested into ChromaDB.
```

If you previously changed the embedding model, re-run this command so the vector store uses the current embedding configuration.

## 6. Start the API backend

Start the FastAPI app in one terminal:

```powershell
cd C:\Users\l76-labuser230610\Treasure-Liquidity-Reporting\treasury-liquidity-assistant
..\treasure\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check the app is alive:

- http://localhost:8000/docs
- http://localhost:8000/health
- http://localhost:8000/metrics

## 7. Start the Streamlit dashboard

Open a second terminal and run:

```powershell
cd C:\Users\l76-labuser230610\Treasure-Liquidity-Reporting\treasury-liquidity-assistant
..\treasure\Scripts\Activate.ps1
streamlit run dashboard/streamlit_app.py
```

Expected result:

- Streamlit launches the dashboard in the browser
- the app shows a scenario selector and a button to generate a report

## 8. Start the monitoring stack with Docker

From the project root:

```powershell
cd C:\Users\l76-labuser230610\Treasure-Liquidity-Reporting\treasury-liquidity-assistant
docker compose up --build -d
```

This starts:

- app
- jaeger
- prometheus
- grafana

Expected local URLs:

- FastAPI app: http://localhost:8000
- Streamlit: http://localhost:8501
- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## 9. Validate the monitoring stack

### 9.1 Prometheus

Open:

- http://localhost:9090/targets

Confirm the `treasury-app` target is `UP`.

### 9.2 Grafana

Open:

- http://localhost:3000

Login:

- username: admin
- password: admin

Make sure the Prometheus datasource is active and the dashboard loads.

### 9.3 Jaeger

Open:

- http://localhost:16686

Search for traces after generating a report.

## 10. Demo scenario 1: Healthy flow

Purpose:

- demonstrate standard operating mode
- confirm metrics and narrative generation work without blocking conditions

Steps:

1. Open Streamlit dashboard
2. Select scenario: `healthy`
3. Enter a run ID such as `demo-healthy-001`
4. Click `Generate draft report`
5. Observe the response

Expected results:

- status is `draft`
- requires human approval = `true`
- metrics are populated
- warnings are empty or minimal
- recommendations are informational
- report is not auto-approved

What to say in the demo:

> This is the normal path. All sources are within expected freshness and metric bounds, so the assistant generates a draft report and requires human review before final sign-off.

### Useful Prometheus queries

```text
treasury_report_requests_total

treasury_last_liquidity_ratio

treasury_last_evaluation_score

treasury_pending_review_reports
```

Expected interpretation:

- report requests are increasing normally
- liquidity ratio is stable
- evaluation score is within acceptable range
- report remains pending review, as intended

## 11. Demo scenario 2: Stale source scenario

Purpose:

- show data freshness drift or stale source issue
- prove the system can detect a stale source before report approval

Steps:

1. Open the dashboard
2. Set scenario to `stale`
3. Enter a run ID such as `demo-stale-001`
4. Click `Generate draft report`
5. Inspect the response

Expected results:

- warnings include stale source notices
- recommendations include refresh or review guidance
- report status may be `DRAFT` or `BLOCKED` depending on the rule path
- `source_freshness` shows the stale source metadata

In Prometheus/Grafana you should see:

- `treasury_source_age_seconds` rising
- `treasury_stale_sources_total` increasing
- `treasury_pending_review_reports` rising or report status flagged

Recommended alert story:

- `TreasurySourceStale` should fire

What to say in the demo:

> One source system stopped refreshing on time. The assistant flags the stale input before release so the analyst can investigate the data before final approval.

### Useful queries

```text
treasury_source_age_seconds

treasury_stale_sources_total

treasury_pending_review_reports
```

## 12. Demo scenario 3: Outlier scenario

Purpose:

- show anomaly detection and metric drift
- demonstrate that a suspicious value is detected before release

Steps:

1. Open the dashboard
2. Set scenario to `outlier`
3. Enter a run ID such as `demo-outlier-001`
4. Click `Generate draft report`
5. Inspect the response

Expected results:

- warnings mention anomaly or evaluation failure
- recommendations mention investigation before sign-off
- evaluation score is below threshold or risk flag is present
- report may be blocked

In Prometheus/Grafana you should see:

- `treasury_last_evaluation_score` drop
- `treasury_pending_review_reports` increase
- `treasury_report_requests_total` increase for the new request

Recommended alert story:

- `LiquidityEvaluationBelowThreshold` should fire

What to say in the demo:

> The report looks numerically suspicious relative to the expected range. The detection layer flags it before the report is approved, which is exactly the operational control a treasury team needs under deadline pressure.

### Useful queries

```text
treasury_last_evaluation_score

treasury_pending_review_reports

sum by (status) (treasury_report_requests_total)
```

## 12. Detailed demo example: full business workflow

This section mirrors the final architecture and the implemented state model.

### 12.1 Architecture in plain English

The system has two parallel paths:

1. Authoritative financial path
   - Treasury analyst triggers a report from Streamlit
   - FastAPI receives the request
   - Orchestrator calls separate source tools for positions, cashflows, and collateral
   - Data is validated and freshness is checked
   - Deterministic calculations run using Python `Decimal`
   - Historical metrics and current calculated values are checked for anomalies
   - Numerical evaluation compares actual metrics with the ground-truth dataset
   - Source lineage is captured so each metric can be traced back to its source numbers
   - A draft report is created

2. Contextual knowledge path
   - Synthetic treasury knowledge docs are loaded and chunked
   - Embeddings are generated
   - ChromaDB stores only guidance text and procedural context
   - RAG retrieval supplies policy and process context to the prompt builder
   - The prompt builder sends deterministic metrics plus guidance into the LLM
   - The LLM provides narrative only, without recalculating or rewriting financial figures

The two paths meet at the draft report, but they remain separate by responsibility.

### 12.2 Demo sequence: healthy path with explicit human approval

Scenario: Normal operating day, no source drift, no critical anomalies, no blocked conditions.

1. Open the Streamlit dashboard.
2. Select scenario: `healthy`.
3. Enter a run ID such as `demo-healthy-001`.
4. Click `Generate draft report`.
5. FastAPI calls the orchestrator.
6. Orchestrator executes these calls in order:
   - `PositionsTool`
   - `CashFlowsTool`
   - `CollateralTool`
7. Each tool reads its own synthetic source JSON file and returns:
   - record count
   - latest extraction timestamp
   - execution time
   - success flag
   - source identity
8. Schema validation runs.
9. Freshness validation evaluates each mandatory source against the configured thresholds.
   - 0 to 30 minutes = `HEALTHY`
   - >30 to 60 minutes = `WARNING`
   - >60 minutes = `CRITICAL`
10. Deterministic calculation service produces the required metrics:
   - `total_cash_position`
   - `total_expected_inflows`
   - `total_expected_outflows`
   - `net_cash_flow`
   - `adjusted_hqla`
   - `simplified_net_cash_outflow`
   - `simplified_liquidity_coverage_ratio`
11. Historical metrics are compared with current values to detect anomalies before review.
12. Numerical evaluation compares the calculated results against the evaluation ground truth dataset.
13. Source lineage is captured for each metric.
14. The system retrieves guidance from ChromaDB and builds the narrative prompt.
15. The LLM generates a draft narrative only.
16. The report is created with state:
   - `report_status = DRAFT`
   - `human_review_status = PENDING_REVIEW`
17. The dashboard or API returns the draft report.
18. The Treasury analyst reviews:
   - metrics
   - anomalies
   - evaluation result
   - source freshness
   - lineage
   - narrative
19. The analyst explicitly chooses `APPROVE`.
20. The application records a review decision with:
   - `review_id`
   - `report_id`
   - `decision`
   - `reviewer`
   - `comment`
   - `reviewed_at`
   - `trace_id`
21. The report becomes:
   - `report_status = APPROVED`
   - `human_review_status = APPROVED`
22. No external submission happens automatically.

Expected demo narration:

> The report is generated through the authoritative financial path, with deterministic calculations and numerical comparison against ground truth. Guidance and narrative are added through the contextual knowledge path. The human analyst must explicitly approve the report before it is finalised. Approval does not auto-submit to a regulator or external system.

### 12.3 Demo sequence: stale source blocking example

Scenario: Payments source data is 65 minutes old.

This is the exact incident flow the runbook should explain.

1. The Treasury analyst opens the dashboard.
2. The dashboard triggers a report generation request.
3. `PositionsTool`, `CashFlowsTool`, and `CollateralTool` read source data.
4. The payments tool returns a source age of 65 minutes.
5. Freshness validation marks the `CashFlowEngine` source as `CRITICAL`.
6. The orchestrator sets the report status to `BLOCKED`.
7. The report remains `PENDING_REVIEW` as a blocked state, but approval is prohibited.
8. The API returns the blocking condition and the review endpoint rejects approval with HTTP 409.
9. The Treasury analyst cannot approve the blocked report.
10. Prometheus shows the stale source metric and alert state.
11. Grafana shows the source age and stale-source trend.
12. Jaeger shows the trace for:
   - source retrieval
   - freshness validation
   - blocked report creation
13. After the source data is refreshed, the report is regenerated.
14. Freshness becomes `HEALTHY`.
15. Numerical evaluation passes.
16. The new report is generated as `DRAFT / PENDING_REVIEW`.
17. Human review approves the refreshed report.
18. Final status becomes `APPROVED`.

Important business point:

> A blocked report is not approved. It is reviewed, remediated, regenerated, and then passed through the same human review gate.

### 12.4 Demo sequence: rejection example

Scenario: Draft report reaches review but the analyst rejects it.

1. Generate a healthy draft report.
2. Review the metrics, narrative, evaluation result, and lineage.
3. Treasury analyst chooses `REJECT`.
4. Application sets:
   - `report_status = REJECTED`
   - `human_review_status = REJECTED`
5. A review record is stored with reviewer, decision, comment, timestamp, and report ID.
6. The rejected report does not return silently to `PENDING_REVIEW`.
7. The report remains rejected until a new version is created or regenerated.

This is the correct state model:

```text
DRAFT / PENDING_REVIEW
        |
        v
Explicit Human Review
       / \
      /   \
   APPROVE  REJECT
      |       |
      v       v
  APPROVED  REJECTED
```

### 12.5 Demo sequence: outlier example

Scenario: Numerical outlier or large daily movement suspiciously changes the liquidity ratio.

1. Generate a report using the outlier scenario.
2. The calculation service computes the metrics.
3. Historical metrics and current values are compared.
4. An anomaly is flagged before human review.
5. The draft report includes the anomaly result and reason.
6. The report may still be generated as a draft, but the anomaly is visible to the Treasury analyst.
7. Observability records the anomaly count in Prometheus.
8. Grafana displays the anomaly-driven signal.
9. Jaeger shows the anomaly detection span and the corresponding report trace.

Expected business message:

> The outlier is detected before human review. The system is not allowing the anomaly to hide inside the narrative. Clear alerting and trace visibility support the analyst review process.

### 12.6 Demonstration observability flow

During every demo, the following should be visible:

- Streamlit triggers a report request
- FastAPI receives the request
- Orchestrator executes retrieval, validation, calculations, evaluation, and RAG lookup
- OpenTelemetry captures spans along the workflow
- OTLP sends spans to Jaeger
- Prometheus scrapes custom metrics
- Grafana shows operational dashboards
- Structured logs capture request and workflow events

### 12.7 Prometheus and Grafana checkpoints

Use these checks after generating a report:

```text
treasury_report_requests_total
treasury_source_age_seconds
treasury_stale_sources_total
treasury_last_liquidity_ratio
treasury_last_evaluation_score
treasury_pending_review_reports
treasury_human_reviews_total
```

Look for:
- a successful report request
- freshness metric drift in stale scenarios
- evaluation failure or pass state
- pending review count
- approval and rejection counters

### 12.8 What to say in the live demo

> This assistant does not replace a Treasury analyst. It retrieves, validates, calculates, and flags risk, while keeping the human in the loop. The authoritative financial path ensures the numbers are deterministic. The knowledge path provides explanatory context. The analyst must review and explicitly approve or reject the final report. No report is auto-submitted to a regulator.

## 13. Troubleshooting

### 13.1 API refuses to start

Check:

- correct Python version is active
- dependencies are installed
- `.env` contains valid values
- `uvicorn` is running from the project root or a correctly configured working directory

### 13.2 ChromaDB is empty or stale

Run:

```powershell
python -m scripts.ingest_knowledge
```

Then verify the vector store is created with the current embedding model.

### 13.3 Prometheus target is down

Check:

- `http://localhost:8000/metrics` is reachable
- the FastAPI app is still running
- Prometheus scrape config is correct
- Docker networking is functioning

### 13.4 Jaeger shows no traces

Check:

- the app is running
- `JAEGER_ENDPOINT` is correct
- OpenTelemetry instrumentation is loaded
- the app route was exercised after startup

### 13.5 Approval is blocked unexpectedly

Review:

- source freshness values
- evaluation pass/fail result
- anomaly conditions
- whether the report was generated in a stale or outlier scenario

## 14. Final summary

This project is a capstone MVP that demonstrates how a Treasury & Liquidity Reporting Assistant can:

- pull deterministic data from three synthetic sources;
- verify source freshness and schema integrity;
- calculate liquidity metrics without changing business numbers;
- detect anomalies before human review;
- compare metrics with ground-truth expectations;
- retrieve contextual guidance through RAG and ChromaDB;
- produce a narrative from the LLM without allowing value overwrites;
- preserve source-to-output lineage;
- require explicit human approval;
- record every review decision;
- never auto-submit to a regulator.

The final workflow is therefore:

Treasury Analyst
-> Streamlit
-> FastAPI
-> Orchestrator
-> retrieval tools
-> validation and calculations
-> anomaly detection
-> RAG retrieval
-> prompt building
-> LLM narrative
-> numerical evaluation
-> lineage capture
-> draft report
-> explicit human review
-> APPROVED or REJECTED

with `BLOCKED` reports prevented from approval until the issue is remediated.
