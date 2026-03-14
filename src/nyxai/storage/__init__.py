"""Storage layer for NyxAI.

This module provides database, cache, and external storage integrations
for the NyxAI AIOps system.
"""

# Import with lazy loading to avoid circular dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyxai.storage.cache import CacheManager, cache_result, get_redis_client
    from nyxai.storage.database import (
        AsyncSessionLocal,
        Base,
        DatabaseManager,
        get_db_session,
        init_db,
    )
    from nyxai.storage.models import Anomaly, Incident, RecoveryAction
    from nyxai.storage.prometheus_client import PrometheusClient, get_prometheus_client


def __getattr__(name: str) -> object:
    """Lazy import to avoid circular dependencies."""
    if name in ("Base", "AsyncSessionLocal", "DatabaseManager", "get_db_session", "init_db"):
        from nyxai.storage.database import (
            AsyncSessionLocal,
            Base,
            DatabaseManager,
            get_db_session,
            init_db,
        )

        return locals()[name]

    if name in ("CacheManager", "cache_result", "get_redis_client"):
        from nyxai.storage.cache import CacheManager, cache_result, get_redis_client

        return locals()[name]

    if name in ("PrometheusClient", "get_prometheus_client"):
        from nyxai.storage.prometheus_client import PrometheusClient, get_prometheus_client

        return locals()[name]

    if name in ("Anomaly", "Incident", "RecoveryAction"):
        from nyxai.storage.models import Anomaly, Incident, RecoveryAction

        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Database
    "Base",
    "AsyncSessionLocal",
    "DatabaseManager",
    "get_db_session",
    "init_db",
    # Cache
    "CacheManager",
    "cache_result",
    "get_redis_client",
    # Prometheus
    "PrometheusClient",
    "get_prometheus_client",
    # Models
    "Anomaly",
    "Incident",
    "RecoveryAction",
]
