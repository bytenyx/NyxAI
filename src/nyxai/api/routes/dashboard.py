"""Dashboard API endpoints for NyxAI.

This module provides REST API endpoints for dashboard statistics and overview.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""

    total_anomalies: int
    open_anomalies: int
    critical_anomalies: int
    recovery_success_rate: float
    recent_anomalies: list[dict[str, Any]]
    metrics_overview: list[dict[str, Any]]


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description="Get overview statistics for the dashboard.",
)
async def get_dashboard_stats() -> DashboardStatsResponse:
    """Get dashboard statistics.

    Returns:
        DashboardStatsResponse: Dashboard statistics including anomaly counts,
        recovery rates, and recent activity.
    """
    # For demonstration, return mock data
    # In production, this would query the database
    return DashboardStatsResponse(
        total_anomalies=156,
        open_anomalies=12,
        critical_anomalies=3,
        recovery_success_rate=94.5,
        recent_anomalies=[
            {
                "id": "anomaly-001",
                "title": "High CPU Usage",
                "service": "api-gateway",
                "severity": "critical",
                "status": "open",
                "detected_at": "2024-03-15T10:30:00Z",
            },
            {
                "id": "anomaly-002",
                "title": "Memory Leak",
                "service": "user-service",
                "severity": "high",
                "status": "acknowledged",
                "detected_at": "2024-03-15T09:15:00Z",
            },
            {
                "id": "anomaly-003",
                "title": "Slow Query",
                "service": "database",
                "severity": "medium",
                "status": "resolved",
                "detected_at": "2024-03-15T08:45:00Z",
            },
        ],
        metrics_overview=[
            {"name": "CPU Usage", "value": 67.5, "trend": -5.2},
            {"name": "Memory Usage", "value": 82.3, "trend": 3.1},
            {"name": "Disk I/O", "value": 45.8, "trend": -2.5},
        ],
    )
