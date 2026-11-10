from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.evaluations import router as evaluations_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.reports import router as reports_router
from app.observability.logging_config import configure_logging
from app.observability.metrics import setup_metrics
from app.observability.tracing import setup_tracing


configure_logging()
logger = logging.getLogger("treasury_app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_metrics()
    setup_tracing(service_name="treasury-liquidity-assistant", app=app)
    logger.info("Application startup complete", extra={"service": "treasury-liquidity-assistant"})
    yield
    logger.info("Application shutdown complete", extra={"service": "treasury-liquidity-assistant"})


app = FastAPI(
    title="Treasury & Liquidity Reporting Assistant",
    description="Educational MVP for treasury liquidity reporting with traceability and review gates.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(reports_router)
app.include_router(evaluations_router)
app.include_router(knowledge_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "Treasury & Liquidity Reporting Assistant",
        "status": "ok",
        "educational_mvp": "true",
        "requirements": "human approval required before any report is released",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: object, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception encountered", extra={"error": exc.__class__.__name__})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
