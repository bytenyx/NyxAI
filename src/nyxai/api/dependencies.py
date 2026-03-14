"""Dependency injection functions for NyxAI API.

This module provides FastAPI dependency functions for database sessions,
cache access, and Prometheus client access.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nyxai.storage.cache import CacheManager, get_redis_client
from nyxai.storage.database import get_db_session
from nyxai.storage.prometheus_client import PrometheusClient, get_prometheus_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession: Database session for the request.

    Raises:
        HTTPException: If database connection fails.
    """
    try:
        async with get_db_session() as session:
            yield session
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from exc


# Type alias for database dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


def get_cache() -> CacheManager:
    """Get cache manager dependency.

    Returns:
        CacheManager: Cache manager instance.

    Raises:
        HTTPException: If cache is not initialized.
    """
    try:
        client = get_redis_client()
        cache_manager = CacheManager()
        cache_manager._redis = client
        return cache_manager
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service not available",
        ) from exc


# Type alias for cache dependency
CacheDep = Annotated[CacheManager, Depends(get_cache)]


def get_prometheus() -> PrometheusClient:
    """Get Prometheus client dependency.

    Returns:
        PrometheusClient: Prometheus client instance.

    Raises:
        HTTPException: If Prometheus client is not initialized.
    """
    try:
        return get_prometheus_client()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus client not available",
        ) from exc


# Type alias for Prometheus dependency
PrometheusDep = Annotated[PrometheusClient, Depends(get_prometheus)]


async def verify_anomaly_exists(anomaly_id: str) -> str:
    """Verify that an anomaly exists.

    This is a placeholder dependency that would typically check the database
    for the existence of an anomaly with the given ID.

    Args:
        anomaly_id: The ID of the anomaly to verify.

    Returns:
        The anomaly ID if it exists.

    Raises:
        HTTPException: If the anomaly does not exist.
    """
    # In a real implementation, this would query the database
    # For now, we just validate the UUID format
    if not anomaly_id or len(anomaly_id) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid anomaly ID",
        )
    return anomaly_id


# Type alias for anomaly ID dependency
AnomalyIdDep = Annotated[str, Depends(verify_anomaly_exists)]
