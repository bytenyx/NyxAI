"""NyxAI API module.

This module provides the REST API for NyxAI, built with FastAPI.
It includes endpoints for anomaly management, metrics querying, and system health checks.
"""

from nyxai.api.main import create_application

__all__ = ["create_application"]
