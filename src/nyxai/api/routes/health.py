"""Health check endpoints for NyxAI API.

This module provides health check endpoints for monitoring the system status,
including basic health, readiness, and liveness checks.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from nyxai.api.models.common import HealthCheckResponse
from nyxai.config import get_settings
from nyxai.storage.cache import get_redis_client
from nyxai.storage.database import get_db_manager
from nyxai.storage.prometheus_client import get_prometheus_client

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Basic health check",
    description="Returns basic health status of the application.",
)
async def health_check() -> HealthCheckResponse:
    """Perform a basic health check.

    Returns:
        HealthCheckResponse: Basic health status information.
    """
    settings = get_settings()
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        checks={
            "application": "up",
            "environment": settings.env,
        },
    )


@router.get(
    "/health/ready",
    response_model=HealthCheckResponse,
    summary="Readiness check",
    description="Checks if the application is ready to serve requests.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Service not ready",
            "model": HealthCheckResponse,
        },
    },
)
async def readiness_check() -> HealthCheckResponse:
    """Check if the application is ready to serve requests.

    This endpoint verifies connections to all required services:
    - Database
    - Redis cache
    - Prometheus

    Returns:
        HealthCheckResponse: Readiness status with detailed checks.

    Raises:
        HTTPException: If any required service is unavailable.
    """
    settings = get_settings()
    checks: dict[str, Any] = {}
    all_healthy = True

    # Check database
    try:
        db_manager = get_db_manager()
        db_healthy = await db_manager.health_check()
        checks["database"] = "healthy" if db_healthy else "unhealthy"
        if not db_healthy:
            all_healthy = False
    except Exception as e:
        checks["database"] = f"unhealthy: {e!s}"
        all_healthy = False

    # Check Redis
    try:
        redis_client = get_redis_client()
        redis_healthy = await redis_client.ping()
        checks["redis"] = "healthy" if redis_healthy else "unhealthy"
        if not redis_healthy:
            all_healthy = False
    except Exception as e:
        checks["redis"] = f"unhealthy: {e!s}"
        all_healthy = False

    # Check Prometheus
    try:
        prom_client = get_prometheus_client()
        prom_healthy = await prom_client.health_check()
        checks["prometheus"] = "healthy" if prom_healthy else "unhealthy"
        if not prom_healthy:
            all_healthy = False
    except Exception as e:
        checks["prometheus"] = f"unhealthy: {e!s}"
        all_healthy = False

    response = HealthCheckResponse(
        status="ready" if all_healthy else "not_ready",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        checks=checks,
    )

    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.model_dump(),
        )

    return response


@router.get(
    "/health/live",
    response_model=HealthCheckResponse,
    summary="Liveness check",
    description="Checks if the application is alive and running.",
)
async def liveness_check() -> HealthCheckResponse:
    """Check if the application is alive.

    This endpoint performs a minimal check to verify the application
    process is running and responsive.

    Returns:
        HealthCheckResponse: Liveness status.
    """
    settings = get_settings()
    return HealthCheckResponse(
        status="alive",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        checks={
            "process": "running",
        },
    )
