"""FastAPI application entry point for NyxAI.

This module creates and configures the FastAPI application with all routes,
middleware, and lifespan management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from nyxai.api.routes import anomalies, auth, health, metrics, rca, recovery, websocket
from nyxai.config import get_settings
from nyxai.storage.cache import close_cache, init_cache
from nyxai.storage.database import close_db, init_db
from nyxai.storage.prometheus_client import close_prometheus_client, init_prometheus_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Manage application lifespan events.

    This context manager handles startup and shutdown events for the application,
    including database connections, cache initialization, and Prometheus client setup.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    # Startup: Initialize all connections
    await init_db()
    await init_cache()
    await init_prometheus_client()

    yield

    # Shutdown: Clean up all connections
    await close_prometheus_client()
    await close_cache()
    await close_db()


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="NyxAI - An Agentic AIOps System for Intelligent Anomaly Detection",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup Prometheus instrumentation
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(anomalies.router, prefix="/api/v1", tags=["anomalies"])
    app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
    app.include_router(recovery.router, prefix="/api/v1", tags=["recovery"])
    app.include_router(rca.router, prefix="/api/v1", tags=["rca"])
    app.include_router(websocket.router, tags=["websocket"])

    return app


# Create the application instance
app = create_application()
