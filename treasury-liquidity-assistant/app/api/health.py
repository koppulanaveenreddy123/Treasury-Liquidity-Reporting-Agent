from __future__ import annotations

import logging

from fastapi import APIRouter

from app.observability.metrics import HEALTH_CHECKS

logger = logging.getLogger("treasury_app")
router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Basic health endpoint used by orchestration and smoke tests."""
    HEALTH_CHECKS.inc()
    logger.info("health check requested", extra={"endpoint": "/health"})
    return {"status": "ok", "service": "treasury-liquidity-assistant"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness check for service startup validation."""
    HEALTH_CHECKS.inc()
    logger.info("readiness check requested", extra={"endpoint": "/ready"})
    return {"status": "ready", "service": "treasury-liquidity-assistant"}
