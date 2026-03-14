"""Pytest configuration and fixtures for NyxAI tests."""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_metric_data():
    """Provide sample metric data for testing."""
    np.random.seed(42)
    n_points = 100
    timestamps = pd.date_range(start="2024-01-01", periods=n_points, freq="1min")
    values = np.random.normal(100, 10, n_points)
    return pd.Series(values, index=timestamps)


@pytest.fixture
def sample_metric_data_with_anomaly():
    """Provide sample metric data with anomalies for testing."""
    np.random.seed(42)
    n_points = 100
    timestamps = pd.date_range(start="2024-01-01", periods=n_points, freq="1min")
    values = np.random.normal(100, 10, n_points)
    # Inject anomalies
    values[20:25] = 150  # Spike
    values[50:55] = 50   # Drop
    return pd.Series(values, index=timestamps)


@pytest.fixture
def sample_anomaly_data():
    """Provide sample anomaly data for testing."""
    return {
        "id": "test-anomaly-001",
        "title": "High CPU Usage",
        "description": "CPU usage exceeded threshold",
        "severity": "high",
        "source_type": "metric",
        "detection_method": "three_sigma",
        "score": 0.85,
        "confidence": 0.9,
        "service_id": "service-a",
        "metric_name": "cpu_usage",
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_service_graph_data():
    """Provide sample service graph data for testing."""
    return {
        "nodes": [
            {"id": "service-a", "name": "Service A", "status": "healthy"},
            {"id": "service-b", "name": "Service B", "status": "degraded"},
            {"id": "service-c", "name": "Service C", "status": "healthy"},
        ],
        "edges": [
            {"source": "service-a", "target": "service-b", "dependency_type": "sync"},
            {"source": "service-b", "target": "service-c", "dependency_type": "sync"},
        ],
    }


@pytest.fixture
def mock_prometheus_response():
    """Provide mock Prometheus API response."""
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "cpu_usage", "service": "test-service"},
                    "value": [1234567890, "75.5"],
                }
            ],
        },
    }


@pytest.fixture
def mock_loki_response():
    """Provide mock Loki API response."""
    return {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"service": "test-service", "level": "error"},
                    "values": [
                        ["1234567890000000000", "Error: connection timeout"],
                    ],
                }
            ],
        },
    }


@pytest.fixture
def sample_recovery_action():
    """Provide sample recovery action for testing."""
    return {
        "id": "test-action-001",
        "action_type": "restart",
        "target": "service-a",
        "parameters": {"graceful": True, "timeout": 30},
        "risk_level": "medium",
        "estimated_duration": 60.0,
        "requires_approval": False,
        "status": "pending",
    }


@pytest.fixture
def sample_incident_record():
    """Provide sample incident record for testing."""
    return {
        "id": "test-incident-001",
        "title": "Service A Outage",
        "description": "Service A experienced high latency",
        "service_id": "service-a",
        "anomaly_type": "high_latency",
        "root_cause": "database_connection_pool_exhausted",
        "solution": "restart_service",
        "severity": "high",
        "status": "resolved",
        "tags": ["latency", "database"],
        "created_at": datetime.utcnow().isoformat(),
    }


class AsyncMock:
    """Helper class for creating async mocks."""

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __call__(self, *args, **kwargs):
        return self.return_value
